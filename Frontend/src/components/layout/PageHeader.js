// frontend/src/components/layout/PageHeader.js
// Reusable page header component

"use client";

import React from "react";

export default function PageHeader({ 
  title, 
  description, 
  actions, 
  breadcrumbs,
  icon 
}) {
  return (
    <div className="bg-white border-b border-gray-200 px-6 py-4">
      {/* Breadcrumbs */}
      {breadcrumbs && (
        <nav className="flex mb-3" aria-label="Breadcrumb">
          <ol className="flex items-center space-x-2 text-sm">
            {breadcrumbs.map((crumb, index) => (
              <li key={index} className="flex items-center">
                {index > 0 && (
                  <svg className="w-4 h-4 text-gray-400 mx-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                )}
                {crumb.href ? (
                  <a href={crumb.href} className="text-gray-500 hover:text-gray-700">
                    {crumb.name}
                  </a>
                ) : (
                  <span className="text-gray-900 font-medium">{crumb.name}</span>
                )}
              </li>
            ))}
          </ol>
        </nav>
      )}

      {/* Header Content */}
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          {icon && (
            <div className="mr-4 text-2xl">
              {icon}
            </div>
          )}
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
            {description && (
              <p className="mt-1 text-sm text-gray-600">{description}</p>
            )}
          </div>
        </div>

        {/* Actions */}
        {actions && (
          <div className="flex items-center space-x-3">
            {actions}
          </div>
        )}
      </div>
    </div>
  );
}