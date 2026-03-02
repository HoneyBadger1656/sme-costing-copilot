// frontend/src/app/costing/page.js
// Automated Costing Module — Formula Library

"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function CostingPage() {
    const [categories, setCategories] = useState([]);
    const [selectedCategory, setSelectedCategory] = useState(null);
    const [selectedFormula, setSelectedFormula] = useState(null);
    const [inputs, setInputs] = useState({});
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(true);
    const [calculating, setCalculating] = useState(false);
    const [searchQuery, setSearchQuery] = useState("");
    const [sidebarOpen, setSidebarOpen] = useState(true);

    // Fetch all formulas on mount
    useEffect(() => {
        fetchFormulas();
    }, []);

    const fetchFormulas = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/api/costing/formulas`);
            if (!response.ok) throw new Error("Failed to fetch formulas");
            const data = await response.json();
            setCategories(data);
            if (data.length > 0) setSelectedCategory(data[0].category_id);
        } catch (error) {
            console.error("Error fetching formulas:", error);
        } finally {
            setLoading(false);
        }
    };

    const selectFormula = (formula) => {
        setSelectedFormula(formula);
        setResult(null);
        // Pre-fill defaults
        const defaults = {};
        formula.inputs.forEach((inp) => {
            defaults[inp.id] = inp.default !== undefined ? inp.default : "";
        });
        setInputs(defaults);
    };

    const handleInputChange = (id, value) => {
        setInputs((prev) => ({ ...prev, [id]: value }));
    };

    const handleCalculate = async (e) => {
        e.preventDefault();
        if (!selectedFormula) return;

        setCalculating(true);
        setResult(null);

        try {
            const token = localStorage.getItem("token");
            const numericInputs = {};
            for (const [key, val] of Object.entries(inputs)) {
                numericInputs[key] = parseFloat(val) || 0;
            }

            const response = await fetch(
                `${API_BASE_URL}/api/costing/formulas/${selectedFormula.id}/calculate`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${token}`,
                    },
                    body: JSON.stringify({ inputs: numericInputs }),
                }
            );

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || "Calculation failed");
            }

            const data = await response.json();
            setResult(data);
        } catch (error) {
            setResult({ error: error.message });
        } finally {
            setCalculating(false);
        }
    };

    // Filter formulas by search
    const getFilteredFormulas = () => {
        if (!searchQuery.trim()) {
            return categories.find((c) => c.category_id === selectedCategory)?.formulas || [];
        }
        const q = searchQuery.toLowerCase();
        const all = [];
        categories.forEach((cat) => {
            cat.formulas.forEach((f) => {
                if (
                    f.name.toLowerCase().includes(q) ||
                    f.description.toLowerCase().includes(q) ||
                    f.formula.toLowerCase().includes(q)
                ) {
                    all.push(f);
                }
            });
        });
        return all;
    };

    const filteredFormulas = getFilteredFormulas();

    const totalFormulaCount = categories.reduce(
        (sum, cat) => sum + cat.formulas.length,
        0
    );

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-950 flex items-center justify-center">
                <div className="text-center">
                    <div className="w-12 h-12 border-4 border-blue-400 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                    <p className="text-gray-400 text-lg">Loading formula library…</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-950 text-gray-100">
            {/* ── Top bar ───────────────────────────────────────────── */}
            <header className="bg-gray-900 border-b border-gray-800 sticky top-0 z-30">
                <div className="max-w-[1800px] mx-auto px-4 py-3 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <Link href="/dashboard" className="text-gray-400 hover:text-white transition text-sm">
                            ← Dashboard
                        </Link>
                        <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                            Automated Costing
                        </h1>
                        <span className="text-xs bg-blue-500/20 text-blue-300 px-2 py-1 rounded-full font-medium">
                            {totalFormulaCount} formulas
                        </span>
                    </div>

                    {/* Search */}
                    <div className="relative w-80">
                        <input
                            type="text"
                            placeholder="Search formulas…"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 pl-10 text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition"
                        />
                        <svg className="absolute left-3 top-2.5 w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                        </svg>
                    </div>
                </div>
            </header>

            <div className="flex max-w-[1800px] mx-auto">
                {/* ── Category sidebar ─────────────────────────────────── */}
                <aside className={`${sidebarOpen ? "w-72" : "w-14"} shrink-0 bg-gray-900 border-r border-gray-800 min-h-[calc(100vh-57px)] transition-all duration-300 sticky top-[57px] self-start`}>
                    <button
                        onClick={() => setSidebarOpen(!sidebarOpen)}
                        className="w-full p-3 text-gray-400 hover:text-white text-xs flex items-center gap-2 border-b border-gray-800"
                    >
                        {sidebarOpen ? "◀ Collapse" : "▶"}
                    </button>

                    {sidebarOpen && (
                        <nav className="p-2 space-y-1">
                            {categories.map((cat) => (
                                <button
                                    key={cat.category_id}
                                    onClick={() => {
                                        setSelectedCategory(cat.category_id);
                                        setSearchQuery("");
                                    }}
                                    className={`w-full text-left px-3 py-2.5 rounded-lg text-sm transition flex items-center gap-2 ${selectedCategory === cat.category_id && !searchQuery
                                            ? "bg-blue-600/20 text-blue-300 border border-blue-500/30"
                                            : "text-gray-400 hover:bg-gray-800 hover:text-gray-200"
                                        }`}
                                >
                                    <span className="text-base">{cat.icon}</span>
                                    <span className="truncate flex-1">{cat.category_name}</span>
                                    <span className="text-xs bg-gray-800 px-1.5 py-0.5 rounded text-gray-500 shrink-0">
                                        {cat.formulas.length}
                                    </span>
                                </button>
                            ))}
                        </nav>
                    )}
                </aside>

                {/* ── Main content area ────────────────────────────────── */}
                <main className="flex-1 p-6">
                    {/* Category header */}
                    {!searchQuery && (
                        <div className="mb-6">
                            <h2 className="text-2xl font-bold text-white">
                                {categories.find((c) => c.category_id === selectedCategory)?.icon}{" "}
                                {categories.find((c) => c.category_id === selectedCategory)?.category_name}
                            </h2>
                            <p className="text-gray-500 text-sm mt-1">
                                {filteredFormulas.length} formula{filteredFormulas.length !== 1 ? "s" : ""} in this category
                            </p>
                        </div>
                    )}
                    {searchQuery && (
                        <div className="mb-6">
                            <h2 className="text-2xl font-bold text-white">
                                Search: &ldquo;{searchQuery}&rdquo;
                            </h2>
                            <p className="text-gray-500 text-sm mt-1">
                                {filteredFormulas.length} result{filteredFormulas.length !== 1 ? "s" : ""}
                            </p>
                        </div>
                    )}

                    {/* Formula grid */}
                    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 mb-8">
                        {filteredFormulas.map((formula) => (
                            <button
                                key={formula.id}
                                onClick={() => selectFormula(formula)}
                                className={`text-left p-5 rounded-xl border transition-all duration-200 group ${selectedFormula?.id === formula.id
                                        ? "bg-blue-600/10 border-blue-500/50 ring-1 ring-blue-500/30"
                                        : "bg-gray-900 border-gray-800 hover:border-gray-600 hover:bg-gray-800/50"
                                    }`}
                            >
                                <h3 className="font-semibold text-white group-hover:text-blue-300 transition text-sm leading-snug">
                                    {formula.name}
                                </h3>
                                <p className="text-xs text-gray-500 mt-2 line-clamp-2">
                                    {formula.description}
                                </p>
                                <div className="mt-3 bg-gray-950/60 rounded-md px-3 py-2 text-xs font-mono text-purple-300 truncate">
                                    {formula.formula}
                                </div>
                            </button>
                        ))}
                    </div>

                    {/* ── Calculator panel ────────────────────────────────── */}
                    {selectedFormula && (
                        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 max-w-2xl mx-auto">
                            <div className="flex items-start justify-between mb-4">
                                <div>
                                    <h3 className="text-xl font-bold text-white">
                                        {selectedFormula.name}
                                    </h3>
                                    <p className="text-gray-400 text-sm mt-1">
                                        {selectedFormula.description}
                                    </p>
                                </div>
                                <button
                                    onClick={() => {
                                        setSelectedFormula(null);
                                        setResult(null);
                                    }}
                                    className="text-gray-500 hover:text-white text-lg"
                                >
                                    ✕
                                </button>
                            </div>

                            {/* Formula display */}
                            <div className="bg-gray-950 rounded-xl px-4 py-3 mb-6 border border-gray-800">
                                <p className="text-sm font-mono text-purple-300">
                                    {selectedFormula.formula}
                                </p>
                            </div>

                            {/* Input fields */}
                            <form onSubmit={handleCalculate}>
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
                                    {selectedFormula.inputs.map((inp) => (
                                        <div key={inp.id}>
                                            <label className="block text-xs font-medium text-gray-400 mb-1.5">
                                                {inp.label}
                                            </label>
                                            <input
                                                type="number"
                                                step="any"
                                                value={inputs[inp.id] ?? ""}
                                                onChange={(e) =>
                                                    handleInputChange(inp.id, e.target.value)
                                                }
                                                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition placeholder-gray-600"
                                                placeholder={
                                                    inp.default !== undefined
                                                        ? `Default: ${inp.default}`
                                                        : "Enter value"
                                                }
                                            />
                                        </div>
                                    ))}
                                </div>

                                <button
                                    type="submit"
                                    disabled={calculating}
                                    className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white py-3 rounded-xl font-semibold hover:from-blue-500 hover:to-purple-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg shadow-blue-500/20"
                                >
                                    {calculating ? (
                                        <span className="flex items-center justify-center gap-2">
                                            <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                                            Calculating…
                                        </span>
                                    ) : (
                                        "Calculate"
                                    )}
                                </button>
                            </form>

                            {/* Result display */}
                            {result && !result.error && (
                                <div className="mt-6 bg-gradient-to-br from-blue-600/10 to-purple-600/10 border border-blue-500/20 rounded-xl p-5 animate-fade-in">
                                    <div className="flex items-end gap-3 mb-3">
                                        <span className="text-4xl font-bold text-white">
                                            {typeof result.result === "number"
                                                ? result.result.toLocaleString("en-IN", {
                                                    maximumFractionDigits: 4,
                                                })
                                                : result.result}
                                        </span>
                                        <span className="text-lg text-gray-400 pb-1">
                                            {result.unit}
                                        </span>
                                    </div>
                                    <pre className="text-sm text-gray-400 whitespace-pre-wrap font-sans leading-relaxed">
                                        {result.explanation}
                                    </pre>
                                </div>
                            )}

                            {result && result.error && (
                                <div className="mt-6 bg-red-500/10 border border-red-500/30 rounded-xl p-4 text-red-300 text-sm">
                                    ⚠ {result.error}
                                </div>
                            )}
                        </div>
                    )}

                    {/* Empty state */}
                    {!selectedFormula && filteredFormulas.length === 0 && (
                        <div className="text-center py-20 text-gray-500">
                            <p className="text-6xl mb-4">🔍</p>
                            <p className="text-lg">No formulas found</p>
                            <p className="text-sm mt-1">
                                Try a different search term or select a category
                            </p>
                        </div>
                    )}
                </main>
            </div>

            <style jsx>{`
        @keyframes fade-in {
          from { opacity: 0; transform: translateY(8px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-fade-in {
          animation: fade-in 0.3s ease-out;
        }
      `}</style>
        </div>
    );
}
