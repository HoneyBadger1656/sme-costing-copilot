# backend/app/services/integration_service.py

from sqlalchemy.orm import Session
from app.models.models import Client, Ledger, Order, IntegrationSync
from typing import Dict, List
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import pandas as pd
import io

class TallyIntegration:
    """
    Tally Prime integration via XML Gateway
    Requires Tally to be running with ODBC/XML server enabled
    """
    
    @staticmethod
    def test_connection(tally_url: str, tally_port: int = 9000) -> Dict:
        """Test connection to Tally"""
        try:
            url = f"http://{tally_url}:{tally_port}"
            
            # Send simple XML request to check connection
            xml_request = """
            <ENVELOPE>
                <HEADER>
                    <VERSION>1</VERSION>
                    <TALLYREQUEST>Export</TALLYREQUEST>
                    <TYPE>Collection</TYPE>
                    <ID>List of Companies</ID>
                </HEADER>
                <BODY>
                    <DESC>
                        <STATICVARIABLES>
                            <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
                        </STATICVARIABLES>
                    </DESC>
                </BODY>
            </ENVELOPE>
            """
            
            response = requests.post(url, data=xml_request, timeout=5)
            
            if response.status_code == 200:
                return {"success": True, "message": "Connected to Tally successfully"}
            else:
                return {"success": False, "message": f"Connection failed with status {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "message": f"Connection error: {str(e)}"}
    
    @staticmethod
    def fetch_ledgers(tally_url: str, tally_port: int, company_name: str) -> List[Dict]:
        """Fetch ledgers from Tally"""
        try:
            url = f"http://{tally_url}:{tally_port}"
            
            xml_request = f"""
            <ENVELOPE>
                <HEADER>
                    <VERSION>1</VERSION>
                    <TALLYREQUEST>Export</TALLYREQUEST>
                    <TYPE>Collection</TYPE>
                    <ID>Ledgers</ID>
                </HEADER>
                <BODY>
                    <DESC>
                        <STATICVARIABLES>
                            <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
                            <SVCURRENTCOMPANY>{company_name}</SVCURRENTCOMPANY>
                        </STATICVARIABLES>
                        <TDL>
                            <TDLMESSAGE>
                                <COLLECTION NAME="Ledgers" ISMODIFY="No">
                                    <TYPE>Ledger</TYPE>
                                    <FETCH>Name, Parent, ClosingBalance</FETCH>
                                </COLLECTION>
                            </TDLMESSAGE>
                        </TDL>
                    </DESC>
                </BODY>
            </ENVELOPE>
            """
            
            response = requests.post(url, data=xml_request, timeout=10)
            
            if response.status_code == 200:
                # Parse XML response
                root = ET.fromstring(response.content)
                ledgers = []
                
                for ledger in root.findall(".//LEDGER"):
                    name = ledger.find("NAME")
                    parent = ledger.find("PARENT")
                    balance = ledger.find("CLOSINGBALANCE")
                    
                    if name is not None:
                        ledgers.append({
                            "name": name.text,
                            "parent": parent.text if parent is not None else "",
                            "balance": float(balance.text) if balance is not None and balance.text else 0
                        })
                
                return ledgers
            else:
                return []
                
        except Exception as e:
            print(f"Error fetching Tally ledgers: {e}")
            return []
    
    @staticmethod
    def sync_ledgers_to_db(
        db: Session,
        client_id: int,
        tally_ledgers: List[Dict]
    ) -> Dict:
        """Sync Tally ledgers to database"""
        
        sync_record = IntegrationSync(
            client_id=client_id,
            integration_type="tally",
            sync_direction="pull",
            entity_type="ledger",
            status="in_progress"
        )
        db.add(sync_record)
        db.commit()
        
        try:
            synced_count = 0
            
            for tally_ledger in tally_ledgers:
                # Determine if receivable or payable based on parent
                parent = tally_ledger.get("parent", "").lower()
                
                if "sundry debtor" in parent or "receivable" in parent:
                    ledger_type = "receivable"
                elif "sundry creditor" in parent or "payable" in parent:
                    ledger_type = "payable"
                else:
                    continue  # Skip other ledger types
                
                # Check if ledger already exists
                existing = db.query(Ledger).filter(
                    Ledger.client_id == client_id,
                    Ledger.party_name == tally_ledger["name"],
                    Ledger.ledger_type == ledger_type
                ).first()
                
                if not existing:
                    # Create new ledger entry
                    ledger = Ledger(
                        client_id=client_id,
                        ledger_type=ledger_type,
                        party_name=tally_ledger["name"],
                        amount=abs(tally_ledger.get("balance", 0)),
                        transaction_date=datetime.utcnow(),
                        status="outstanding" if tally_ledger.get("balance", 0) != 0 else "paid",
                        reference_type="tally_sync"
                    )
                    db.add(ledger)
                    synced_count += 1
            
            db.commit()
            
            sync_record.status = "success"
            sync_record.records_synced = synced_count
            sync_record.completed_at = datetime.utcnow()
            db.commit()
            
            return {
                "success": True,
                "records_synced": synced_count,
                "message": f"Synced {synced_count} ledgers from Tally"
            }
            
        except Exception as e:
            sync_record.status = "failed"
            sync_record.error_message = str(e)
            sync_record.completed_at = datetime.utcnow()
            db.commit()
            
            return {
                "success": False,
                "message": f"Sync failed: {str(e)}"
            }


class ZohoIntegration:
    """
    Zoho Books integration via REST API
    """
    
    BASE_URL = "https://books.zoho.in/api/v3"
    
    @staticmethod
    def get_auth_url(client_id: str, redirect_uri: str, scope: str = "ZohoBooks.fullaccess.all") -> str:
        """Generate OAuth URL for user authorization"""
        return f"https://accounts.zoho.in/oauth/v2/auth?scope={scope}&client_id={client_id}&response_type=code&redirect_uri={redirect_uri}&access_type=offline"
    
    @staticmethod
    def exchange_code_for_tokens(
        code: str,
        client_id: str,
        client_secret: str,
        redirect_uri: str
    ) -> Dict:
        """Exchange authorization code for access token"""
        try:
            response = requests.post(
                "https://accounts.zoho.in/oauth/v2/token",
                data={
                    "code": code,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code"
                }
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": "Token exchange failed"}
                
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def refresh_access_token(refresh_token: str, client_id: str, client_secret: str) -> Dict:
        """Refresh expired access token"""
        try:
            response = requests.post(
                "https://accounts.zoho.in/oauth/v2/token",
                data={
                    "refresh_token": refresh_token,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "grant_type": "refresh_token"
                }
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": "Token refresh failed"}
                
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def fetch_invoices(
        access_token: str,
        organization_id: str,
        status: str = "unpaid"
    ) -> List[Dict]:
        """Fetch invoices from Zoho Books"""
        try:
            headers = {
                "Authorization": f"Zoho-oauthtoken {access_token}"
            }
            
            params = {
                "organization_id": organization_id,
                "status": status
            }
            
            response = requests.get(
                f"{ZohoIntegration.BASE_URL}/invoices",
                headers=headers,
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("invoices", [])
            else:
                return []
                
        except Exception as e:
            print(f"Error fetching Zoho invoices: {e}")
            return []
    
    @staticmethod
    def sync_invoices_to_db(
        db: Session,
        client_id: int,
        zoho_invoices: List[Dict]
    ) -> Dict:
        """Sync Zoho invoices to database as receivables"""
        
        sync_record = IntegrationSync(
            client_id=client_id,
            integration_type="zoho",
            sync_direction="pull",
            entity_type="invoice",
            status="in_progress"
        )
        db.add(sync_record)
        db.commit()
        
        try:
            synced_count = 0
            
            for invoice in zoho_invoices:
                # Check if already synced
                existing = db.query(Ledger).filter(
                    Ledger.client_id == client_id,
                    Ledger.reference_type == "zoho_invoice",
                    Ledger.reference_id == int(invoice.get("invoice_id", 0))
                ).first()
                
                if not existing:
                    ledger = Ledger(
                        client_id=client_id,
                        ledger_type="receivable",
                        party_name=invoice.get("customer_name", ""),
                        amount=float(invoice.get("balance", 0)),
                        transaction_date=datetime.strptime(invoice.get("date", ""), "%Y-%m-%d") if invoice.get("date") else datetime.utcnow(),
                        due_date=datetime.strptime(invoice.get("due_date", ""), "%Y-%m-%d") if invoice.get("due_date") else None,
                        status="outstanding" if float(invoice.get("balance", 0)) > 0 else "paid",
                        reference_type="zoho_invoice",
                        reference_id=int(invoice.get("invoice_id", 0)),
                        notes=f"Invoice #{invoice.get('invoice_number', '')}"
                    )
                    db.add(ledger)
                    synced_count += 1
            
            db.commit()
            
            sync_record.status = "success"
            sync_record.records_synced = synced_count
            sync_record.completed_at = datetime.utcnow()
            db.commit()
            
            return {
                "success": True,
                "records_synced": synced_count,
                "message": f"Synced {synced_count} invoices from Zoho Books"
            }
            
        except Exception as e:
            sync_record.status = "failed"
            sync_record.error_message = str(e)
            sync_record.completed_at = datetime.utcnow()
            db.commit()
            
            return {
                "success": False,
                "message": f"Sync failed: {str(e)}"
            }


class ExcelCSVImport:
    """Handle Excel and CSV file imports"""
    
    @staticmethod
    def import_orders_from_file(
        db: Session,
        client_id: int,
        file_content: bytes,
        filename: str
    ) -> Dict:
        """Import orders from Excel or CSV file"""
        
        try:
            # Determine file type and read
            if filename.endswith('.csv'):
                df = pd.read_csv(io.BytesIO(file_content))
            elif filename.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(io.BytesIO(file_content))
            else:
                return {"success": False, "message": "Unsupported file format"}
            
            # Expected columns: customer_name, product_name, quantity, selling_price, cost_price, credit_days
            required_cols = ["customer_name", "quantity", "selling_price", "cost_price"]
            
            if not all(col in df.columns for col in required_cols):
                return {
                    "success": False,
                    "message": f"Missing required columns. Need: {', '.join(required_cols)}"
                }
            
            imported_count = 0
            errors = []
            
            for idx, row in df.iterrows():
                try:
                    # Create order
                    order = Order(
                        client_id=client_id,
                        order_number=f"IMP-{datetime.utcnow().strftime('%Y%m%d')}-{idx+1}",
                        customer_name=str(row["customer_name"]),
                        order_date=datetime.utcnow(),
                        total_cost=float(row["cost_price"]) * float(row["quantity"]),
                        total_selling_price=float(row["selling_price"]) * float(row["quantity"]),
                        credit_days=int(row.get("credit_days", 30)),
                        status="confirmed"
                    )
                    
                    # Calculate margin
                    order.gross_margin = order.total_selling_price - order.total_cost
                    if order.total_selling_price > 0:
                        order.margin_percentage = (order.gross_margin / order.total_selling_price) * 100
                    
                    db.add(order)
                    imported_count += 1
                    
                except Exception as e:
                    errors.append(f"Row {idx+2}: {str(e)}")
            
            db.commit()
            
            return {
                "success": True,
                "imported_count": imported_count,
                "errors": errors,
                "message": f"Imported {imported_count} orders successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Import failed: {str(e)}"
            }
    
    @staticmethod
    def import_products_from_file(
        db: Session,
        client_id: int,
        file_content: bytes,
        filename: str
    ) -> Dict:
        """Import products from Excel or CSV file"""
        
        try:
            if filename.endswith('.csv'):
                df = pd.read_csv(io.BytesIO(file_content))
            elif filename.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(io.BytesIO(file_content))
            else:
                return {"success": False, "message": "Unsupported file format"}
            
            # Expected: name, category, raw_material_cost, labour_cost_per_unit, overhead_percentage, target_margin_percentage
            required_cols = ["name", "raw_material_cost", "labour_cost_per_unit"]
            
            if not all(col in df.columns for col in required_cols):
                return {
                    "success": False,
                    "message": f"Missing required columns. Need: {', '.join(required_cols)}"
                }
            
            from app.models.models import Product
            
            imported_count = 0
            errors = []
            
            for idx, row in df.iterrows():
                try:
                    product = Product(
                        client_id=client_id,
                        name=str(row["name"]),
                        category=str(row.get("category", "")),
                        unit=str(row.get("unit", "pcs")),
                        raw_material_cost=float(row["raw_material_cost"]),
                        labour_cost_per_unit=float(row["labour_cost_per_unit"]),
                        overhead_percentage=float(row.get("overhead_percentage", 10)),
                        target_margin_percentage=float(row.get("target_margin_percentage", 20)),
                        tax_rate=float(row.get("tax_rate", 18))
                    )
                    
                    db.add(product)
                    imported_count += 1
                    
                except Exception as e:
                    errors.append(f"Row {idx+2}: {str(e)}")
            
            db.commit()
            
            return {
                "success": True,
                "imported_count": imported_count,
                "errors": errors,
                "message": f"Imported {imported_count} products successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Import failed: {str(e)}"
            }
