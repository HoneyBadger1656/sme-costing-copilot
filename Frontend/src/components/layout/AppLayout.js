// frontend/src/components/layout/AppLayout.js
// Main application layout wrapper component

"use client";

import React from "react";
import { NavigationProvider } from "../navigation/NavigationProvider";
import Sidebar from "../navigation/Sidebar";
import TopNav from "../navigation/TopNav";
import MobileDrawer from "./MobileDrawer";

export default function AppLayout({ children }) {
  return (
    <NavigationProvider>
      <div className="flex h-screen bg-gray-50">
        {/* Desktop Sidebar */}
        <div className="hidden md:flex">
          <Sidebar />
        </div>

        {/* Mobile Drawer */}
        <MobileDrawer />

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Top Navigation */}
          <TopNav />

          {/* Page Content */}
          <main className="flex-1 overflow-y-auto">
            {children}
          </main>
        </div>
      </div>
    </NavigationProvider>
  );
}