// frontend/src/components/ui/Card.js
// Reusable card component

"use client";

import React from "react";

export default function Card({ 
  children, 
  className = "", 
  padding = "p-6",
  hover = false 
}) {
  const baseClasses = "bg-white rounded-lg shadow border border-gray-200";
  const hoverClasses = hover ? "hover:shadow-md transition-shadow duration-200" : "";
  
  const classes = `${baseClasses} ${hoverClasses} ${padding} ${className}`;

  return (
    <div className={classes}>
      {children}
    </div>
  );
}

export function CardHeader({ children, className = "" }) {
  return (
    <div className={`border-b border-gray-200 pb-4 mb-4 ${className}`}>
      {children}
    </div>
  );
}

export function CardTitle({ children, className = "" }) {
  return (
    <h3 className={`text-lg font-semibold text-gray-900 ${className}`}>
      {children}
    </h3>
  );
}

export function CardContent({ children, className = "" }) {
  return (
    <div className={className}>
      {children}
    </div>
  );
}