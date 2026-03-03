// frontend/src/components/layout/MobileDrawer.js
// Mobile navigation drawer component

"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useNavigation } from "../navigation/NavigationProvider";

const navigationItems = [
  {
    name: "Dashboard",
    href: "/dashboard",
    icon: "🏠",
    description: "Overview and analytics"
  },
  {
    name: "Automated Costing",
    href: "/costing",
    icon: "📊",
    description: "Formula library and calculations"
  },
  {
    name: "Financial Management",
    href: "/financial-management",
    icon: "💰",
    description: "Financial ratios and analysis"
  },
  {
    name: "Scenario Manager",
    href: "/scenarios",
    icon: "🔄",
    description: "What-if analysis"
  },
  {
    name: "AI Assistant",
    href: "/assistant",
    icon: "🤖",
    description: "Financial AI chat"
  },
  {
    name: "Order Evaluation",
    href: "/evaluate",
    icon: "📈",
    description: "Evaluate order profitability"
  },
  {
    name: "Products",
    href: "/products",
    icon: "📦",
    description: "Product management and BOM"
  },
  {
    name: "Clients",
    href: "/clients",
    icon: "👥",
    description: "Client management"
  },
  {
    name: "Financial Data",
    href: "/financial-data",
    icon: "📄",
    description: "Upload financial statements"
  },
  {
    name: "Integrations",
    href: "/integrations",
    icon: "🔗",
    description: "Tally, Zoho connections"
  }
];

export default function MobileDrawer() {
  const pathname = usePathname();
  const { showMobileMenu, setShowMobileMenu } = useNavigation();

  const isActive = (href) => {
    if (href === "/dashboard") {
      return pathname === "/" || pathname === "/dashboard";
    }
    return pathname.startsWith(href);
  };

  const handleLinkClick = () => {
    setShowMobileMenu(false);
  };

  return (
    <>
      {/* Overlay */}
      {showMobileMenu && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 md:hidden"
          onClick={() => setShowMobileMenu(false)}
        />
      )}

      {/* Mobile Drawer */}
      <div className={`fixed inset-y-0 left-0 z-50 w-64 bg-gray-900 text-white transform transition-transform duration-300 ease-in-out md:hidden ${
        showMobileMenu ? "translate-x-0" : "-translate-x-full"
      }`}>
        
        {/* Header */}
        <div className="p-4 border-b border-gray-800">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-lg font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                SME Costing Copilot
              </h1>
              <p className="text-xs text-gray-400 mt-1">Financial Management Platform</p>
            </div>
            <button
              onClick={() => setShowMobileMenu(false)}
              className="p-2 rounded-lg hover:bg-gray-800 transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-2 py-4 space-y-1 overflow-y-auto">
          {navigationItems.map((item) => {
            const active = isActive(item.href);
            return (
              <Link
                key={item.name}
                href={item.href}
                onClick={handleLinkClick}
                className={`group flex items-center px-3 py-2.5 text-sm font-medium rounded-lg transition-all duration-200 ${
                  active
                    ? "bg-blue-600 text-white shadow-lg shadow-blue-500/20"
                    : "text-gray-300 hover:bg-gray-800 hover:text-white"
                }`}
              >
                <span className="text-lg mr-3 flex-shrink-0">{item.icon}</span>
                <div className="flex-1 min-w-0">
                  <div className="truncate">{item.name}</div>
                  <div className="text-xs text-gray-400 truncate">{item.description}</div>
                </div>
                {active && (
                  <div className="w-2 h-2 bg-white rounded-full flex-shrink-0"></div>
                )}
              </Link>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-gray-800">
          <div className="text-xs text-gray-400">
            <div>Version 1.0.0</div>
            <div className="mt-1">© 2026 SME Costing Copilot</div>
          </div>
        </div>
      </div>
    </>
  );
}