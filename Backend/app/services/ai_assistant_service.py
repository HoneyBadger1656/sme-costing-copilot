# backend/app/services/ai_assistant_service.py

from sqlalchemy.orm import Session
from app.models.models import ChatMessage, Client, Order, Product, Ledger, Scenario, IntegrationSync
from typing import Dict, List
import json
import os

# Initialize AI client (Groq preferred, fallback to OpenAI)
client = None
client_type = None

if os.getenv("GROQ_API_KEY"):
    from groq import Groq
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    client_type = "groq"
elif os.getenv("OPENAI_API_KEY"):
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    client_type = "openai"

class AIAssistantService:
    
    @staticmethod
    def chat(db: Session, client_id: int, user_message: str) -> Dict:
        """
        Process user query and generate AI response
        Uses RAG pattern: retrieve relevant data, then generate answer
        Enhanced with conversation memory
        """
        
        # Classify query type
        query_type = AIAssistantService._classify_query(user_message)
        
        # Retrieve relevant data based on query type
        context_data = AIAssistantService._retrieve_context(db, client_id, query_type, user_message)
        
        # Get recent conversation history for context
        recent_messages = AIAssistantService.get_conversation_history(db, client_id, limit=10)
        
        # Build prompt with context and conversation memory
        system_prompt = AIAssistantService._build_system_prompt()
        user_prompt = AIAssistantService._build_user_prompt(user_message, context_data, recent_messages)
        
        # Call LLM
        try:
            if not client:
                return {
                    "message": "AI Assistant is not configured. Please set GROQ_API_KEY or OPENAI_API_KEY environment variable to enable AI features.\n\nGet your Groq API key free at: https://console.groq.com/keys",
                    "query_type": "error",
                    "data_used": context_data
                }
            
            messages = [
                {"role": "system", "content": system_prompt}
            ]
            
            # Add recent conversation history for context (last 5 messages)
            if recent_messages:
                for msg in recent_messages[-5:]:
                    messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
            
            # Add current user message
            messages.append({"role": "user", "content": user_prompt})
            
            if client_type == "groq":
                response = client.chat.completions.create(
                    model="llama3-8b-8192",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1000
                )
            else:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1000
                )
            
            assistant_message = response.choices[0].message.content
            
            # Save conversation
            db.add(ChatMessage(
                client_id=client_id,
                role="user",
                content=user_message,
                query_type=query_type
            ))
            
            db.add(ChatMessage(
                client_id=client_id,
                role="assistant",
                content=assistant_message,
                query_type=query_type,
                data_retrieved=context_data
            ))
            
            db.commit()
            
            return {
                "message": assistant_message,
                "query_type": query_type,
                "data_used": context_data
            }
            
        except Exception as e:
            return {
                "message": f"Sorry, I encountered an error: {str(e)}",
                "query_type": "error",
                "data_used": {}
            }
    
    @staticmethod
    def _classify_query(message: str) -> str:
        """Classify user query into categories using LLM for better accuracy"""
        message_lower = message.lower()
        
        # Enhanced keyword-based classification with more categories
        if any(word in message_lower for word in ["scenario", "what if", "compare scenario", "best scenario"]):
            return "scenarios"
        elif any(word in message_lower for word in ["ratio", "wacc", "roe", "current ratio", "debt equity", "formula"]):
            return "financial_formulas"
        elif any(word in message_lower for word in ["tally", "zoho", "integration", "sync", "connection", "import"]):
            return "integration_status"
        elif any(word in message_lower for word in ["margin", "profit", "profitable", "loss"]):
            return "profitability"
        elif any(word in message_lower for word in ["cash", "receivable", "payment", "collection", "overdue"]):
            return "cash_flow"
        elif any(word in message_lower for word in ["cost", "price", "costing", "expense"]):
            return "costing"
        elif any(word in message_lower for word in ["customer", "client", "who", "which customer"]):
            return "customer_analysis"
        elif any(word in message_lower for word in ["order", "sale", "revenue"]):
            return "orders"
        else:
            return "general"
    
    @staticmethod
    def _retrieve_context(db: Session, client_id: int, query_type: str, message: str) -> Dict:
        """Retrieve relevant data from database based on query type"""
        context = {}
        
        from datetime import datetime, timedelta
        
        if query_type == "profitability":
            # Get recent orders with margins
            orders = db.query(Order).filter(
                Order.client_id == client_id,
                Order.created_at >= datetime.utcnow() - timedelta(days=30)
            ).order_by(Order.margin_percentage.desc()).limit(10).all()
            
            context["recent_orders"] = [
                {
                    "customer": o.customer_name,
                    "revenue": o.total_selling_price,
                    "margin": o.gross_margin,
                    "margin_percent": o.margin_percentage,
                    "date": o.order_date.strftime("%Y-%m-%d")
                }
                for o in orders
            ]
            
            # Aggregate stats
            all_orders = db.query(Order).filter(
                Order.client_id == client_id,
                Order.created_at >= datetime.utcnow() - timedelta(days=30)
            ).all()
            
            if all_orders:
                total_revenue = sum(o.total_selling_price for o in all_orders)
                total_margin = sum(o.gross_margin for o in all_orders)
                avg_margin_pct = (total_margin / total_revenue * 100) if total_revenue > 0 else 0
                
                context["summary"] = {
                    "total_revenue": round(total_revenue, 2),
                    "total_margin": round(total_margin, 2),
                    "avg_margin_percent": round(avg_margin_pct, 2),
                    "order_count": len(all_orders)
                }
        
        elif query_type == "cash_flow":
            # Get receivables
            receivables = db.query(Ledger).filter(
                Ledger.client_id == client_id,
                Ledger.ledger_type == "receivable",
                Ledger.status == "outstanding"
            ).all()
            
            now = datetime.utcnow()
            overdue = [r for r in receivables if r.due_date and r.due_date < now]
            
            context["receivables"] = {
                "total_outstanding": round(sum(r.amount for r in receivables), 2),
                "overdue_amount": round(sum(r.amount for r in overdue), 2),
                "overdue_count": len(overdue)
            }
            
            if overdue:
                context["top_overdue"] = [
                    {
                        "party": r.party_name,
                        "amount": r.amount,
                        "days_overdue": (now - r.due_date).days
                    }
                    for r in sorted(overdue, key=lambda x: x.amount, reverse=True)[:5]
                ]
        
        elif query_type == "costing":
            # Get products
            products = db.query(Product).filter(
                Product.client_id == client_id,
                Product.is_active == True
            ).all()
            
            context["products"] = [
                {
                    "name": p.name,
                    "rm_cost": p.raw_material_cost,
                    "labour_cost": p.labour_cost_per_unit,
                    "target_margin": p.target_margin_percentage
                }
                for p in products[:10]
            ]
        
        elif query_type == "customer_analysis":
            # Get customer-wise revenue
            from sqlalchemy import func
            
            customer_stats = db.query(
                Order.customer_name,
                func.count(Order.id).label("order_count"),
                func.sum(Order.total_selling_price).label("total_revenue"),
                func.sum(Order.gross_margin).label("total_margin")
            ).filter(
                Order.client_id == client_id,
                Order.created_at >= datetime.utcnow() - timedelta(days=90)
            ).group_by(Order.customer_name).all()
            
            context["customers"] = [
                {
                    "name": c.customer_name,
                    "orders": c.order_count,
                    "revenue": round(c.total_revenue or 0, 2),
                    "margin": round(c.total_margin or 0, 2),
                    "margin_percent": round((c.total_margin / c.total_revenue * 100) if c.total_revenue else 0, 2)
                }
                for c in sorted(customer_stats, key=lambda x: x.total_revenue or 0, reverse=True)[:10]
            ]
        
        elif query_type == "orders":
            # Recent orders
            orders = db.query(Order).filter(
                Order.client_id == client_id
            ).order_by(Order.order_date.desc()).limit(10).all()
            
            context["recent_orders"] = [
                {
                    "customer": o.customer_name,
                    "revenue": o.total_selling_price,
                    "status": o.status,
                    "date": o.order_date.strftime("%Y-%m-%d")
                }
                for o in orders
            ]
        
        elif query_type == "scenarios":
            # Get recent scenarios and their results
            scenarios = db.query(Scenario).filter(
                Scenario.client_id == client_id
            ).order_by(Scenario.created_at.desc()).limit(10).all()
            
            context["scenarios"] = [
                {
                    "name": s.name,
                    "description": s.description,
                    "changes": s.changes,
                    "revenue_impact": s.impact_summary.get("revenue_change", 0),
                    "margin_impact": s.impact_summary.get("margin_change", 0),
                    "wc_impact": s.impact_summary.get("wc_change", 0),
                    "recommendation": s.impact_summary.get("recommendation", ""),
                    "created_date": s.created_at.strftime("%Y-%m-%d")
                }
                for s in scenarios
            ]
            
            # Find best scenarios
            if scenarios:
                best_profit = max(scenarios, key=lambda x: x.impact_summary.get("margin_change", 0))
                best_cash = min(scenarios, key=lambda x: x.impact_summary.get("wc_change", 0))
                
                context["best_scenarios"] = {
                    "best_for_profit": best_profit.name,
                    "best_for_cash": best_cash.name
                }
        
        elif query_type == "financial_formulas":
            # Get available financial formulas and recent calculations
            # This would integrate with the financial formulas service once implemented
            context["available_formulas"] = [
                "Current Ratio", "Quick Ratio", "Debt-to-Equity Ratio", 
                "Working Capital", "WACC", "ROE", "ROCE", 
                "Gross Profit Margin", "Net Profit Margin"
            ]
            
            # Get basic financial data for formula calculations
            orders = db.query(Order).filter(
                Order.client_id == client_id,
                Order.created_at >= datetime.utcnow() - timedelta(days=30)
            ).all()
            
            if orders:
                total_revenue = sum(o.total_selling_price for o in orders)
                total_cost = sum(o.total_cost for o in orders)
                total_margin = total_revenue - total_cost
                
                context["financial_data"] = {
                    "total_revenue": round(total_revenue, 2),
                    "total_cost": round(total_cost, 2),
                    "gross_margin": round(total_margin, 2),
                    "gross_margin_percent": round((total_margin / total_revenue * 100) if total_revenue > 0 else 0, 2)
                }
        
        elif query_type == "integration_status":
            # Get integration sync status
            integrations = db.query(IntegrationSync).filter(
                IntegrationSync.client_id == client_id
            ).order_by(IntegrationSync.last_sync.desc()).all()
            
            context["integrations"] = [
                {
                    "source": i.source_type,
                    "status": i.status,
                    "last_sync": i.last_sync.strftime("%Y-%m-%d %H:%M") if i.last_sync else "Never",
                    "records_synced": i.records_synced,
                    "error_message": i.error_message
                }
                for i in integrations
            ]
            
            # Summary
            active_integrations = [i for i in integrations if i.status == "success"]
            context["integration_summary"] = {
                "total_integrations": len(integrations),
                "active_integrations": len(active_integrations),
                "last_successful_sync": max([i.last_sync for i in active_integrations]) if active_integrations else None
            }
        
        return context
    
    @staticmethod
    def _build_system_prompt() -> str:
        """Build system prompt for AI assistant"""
        return """You are a financial assistant for Indian SMEs. Your role is to:

1. Answer finance and business questions in simple, plain language
2. Use the provided data to give specific, actionable insights
3. Explain financial concepts without jargon
4. Give concrete recommendations when asked
5. Always cite numbers from the data when available
6. Analyze uploaded documents and provide business insights
7. Help with scenario analysis and financial planning
8. Provide integration status and data sync information

Guidelines:
- Keep answers under 200 words unless complex analysis needed
- Use Indian Rupee (₹) for all amounts
- Format large numbers with commas (e.g., ₹1,50,000)
- If data is insufficient, say so and suggest what data would help
- Be direct and practical - SME owners want actionable advice, not theory
- Remember previous conversation context to provide connected responses

When analyzing margins:
- Below 10% = concerning
- 10-15% = acceptable
- Above 15% = healthy
- Above 20% = excellent

When analyzing cash flow:
- Overdue > 30 days = immediate action needed
- Working capital > 60 days of revenue = potential cash crunch

When analyzing scenarios:
- Focus on profit vs cash flow trade-offs
- Highlight the most balanced option
- Explain risks and opportunities

When analyzing uploaded files:
- Extract key financial insights
- Identify trends and patterns
- Provide actionable recommendations
- Compare with existing business data when possible"""
    
    @staticmethod
    def _build_user_prompt(user_message: str, context_data: Dict, recent_messages: List[Dict] = None) -> str:
        """Build user prompt with context and conversation memory"""
        prompt = f"User question: {user_message}\n\n"
        
        if context_data:
            prompt += "Relevant data from their business:\n"
            prompt += json.dumps(context_data, indent=2)
            prompt += "\n\nUse this data to answer their question specifically."
        else:
            prompt += "No specific data available. Provide general guidance."
        
        # Add conversation context if available
        if recent_messages and len(recent_messages) > 0:
            prompt += "\n\nRecent conversation context (for reference):\n"
            for msg in recent_messages[-3:]:  # Last 3 messages for context
                role = "User" if msg["role"] == "user" else "Assistant"
                prompt += f"{role}: {msg['content'][:100]}...\n"
            prompt += "\nUse this context to provide more relevant and connected responses."
        
        return prompt
    
    @staticmethod
    def get_conversation_history(db: Session, client_id: int, limit: int = 20) -> List[Dict]:
        """Retrieve recent conversation history"""
        messages = db.query(ChatMessage).filter(
            ChatMessage.client_id == client_id
        ).order_by(ChatMessage.created_at.desc()).limit(limit).all()
        
        # Reverse to get chronological order
        messages.reverse()
        
        return [
            {
                "role": m.role,
                "content": m.content,
                "timestamp": m.created_at.isoformat()
            }
            for m in messages
        ]
    
    @staticmethod
    def chat_with_file(db: Session, client_id: int, user_message: str, file_name: str, file_content: str) -> Dict:
        """
        Process user query with uploaded file content
        """
        
        # Classify as file analysis
        query_type = "file_analysis"
        
        # Build context with file content
        context_data = {
            "file_name": file_name,
            "file_content": file_content[:3000],  # Limit content
            "file_type": "document"
        }
        
        # Get recent conversation history for context
        recent_messages = AIAssistantService.get_conversation_history(db, client_id, limit=5)
        
        # Build prompt with file context
        system_prompt = AIAssistantService._build_system_prompt()
        user_prompt = f"""User uploaded a file: {file_name}

User question: {user_message}

File content:
{file_content}

Please analyze this file and answer the user's question. Focus on:
1. Key insights from the data
2. Financial implications if applicable
3. Actionable recommendations
4. Any patterns or trends you notice

Keep your response practical and business-focused."""
        
        # Call LLM
        try:
            if not client:
                return {
                    "message": "AI Assistant is not configured. Please set GROQ_API_KEY or OPENAI_API_KEY environment variable to enable AI features.",
                    "query_type": "error",
                    "data_used": context_data
                }
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            if client_type == "groq":
                response = client.chat.completions.create(
                    model="llama3-8b-8192",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1500  # More tokens for file analysis
                )
            else:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1500
                )
            
            assistant_message = response.choices[0].message.content
            
            # Save conversation with file context
            db.add(ChatMessage(
                client_id=client_id,
                role="user",
                content=f"[File: {file_name}] {user_message}",
                query_type=query_type
            ))
            
            db.add(ChatMessage(
                client_id=client_id,
                role="assistant",
                content=assistant_message,
                query_type=query_type,
                data_retrieved=context_data
            ))
            
            db.commit()
            
            return {
                "message": assistant_message,
                "query_type": query_type,
                "data_used": context_data
            }
            
        except Exception as e:
            return {
                "message": f"Sorry, I encountered an error analyzing the file: {str(e)}",
                "query_type": "error",
                "data_used": {}
            }
