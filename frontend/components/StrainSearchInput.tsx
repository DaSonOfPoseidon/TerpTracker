"use client"

import { useState, useRef, useEffect, useCallback } from "react"
import { autocompleteStrains, analyzeStrain } from "@/lib/api"
import { AnalysisResult, StrainSuggestion } from "@/lib/types"
import { Input } from "./ui/input"
import { Loader2 } from "lucide-react"

const categoryDotColors: Record<string, string> = {
  BLUE: "bg-blue-500",
  YELLOW: "bg-yellow-400",
  PURPLE: "bg-purple-600",
  GREEN: "bg-green-600",
  ORANGE: "bg-orange-500",
  RED: "bg-red-600",
}

interface StrainSearchInputProps {
  onResult: (result: AnalysisResult | null) => void
}

export function StrainSearchInput({ onResult }: StrainSearchInputProps) {
  const [query, setQuery] = useState("")
  const [suggestions, setSuggestions] = useState<StrainSuggestion[]>([])
  const [showDropdown, setShowDropdown] = useState(false)
  const [activeIndex, setActiveIndex] = useState(-1)
  const [loading, setLoading] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const debounceRef = useRef<ReturnType<typeof setTimeout>>()

  const fetchSuggestions = useCallback(async (q: string) => {
    if (q.length < 2) {
      setSuggestions([])
      setShowDropdown(false)
      return
    }

    setLoading(true)
    try {
      const results = await autocompleteStrains(q)
      setSuggestions(results)
      setShowDropdown(results.length > 0)
      setActiveIndex(-1)
    } catch {
      setSuggestions([])
    } finally {
      setLoading(false)
    }
  }, [])

  const handleInputChange = (value: string) => {
    setQuery(value)
    setError(null)

    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => fetchSuggestions(value), 300)
  }

  const selectStrain = async (name: string) => {
    setQuery(name)
    setShowDropdown(false)
    setSuggestions([])
    setError(null)
    setAnalyzing(true)
    onResult(null)

    try {
      const result = await analyzeStrain(name)
      onResult(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to analyze strain")
      onResult(null)
    } finally {
      setAnalyzing(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!showDropdown || suggestions.length === 0) return

    if (e.key === "ArrowDown") {
      e.preventDefault()
      setActiveIndex(prev => Math.min(prev + 1, suggestions.length - 1))
    } else if (e.key === "ArrowUp") {
      e.preventDefault()
      setActiveIndex(prev => Math.max(prev - 1, 0))
    } else if (e.key === "Enter" && activeIndex >= 0) {
      e.preventDefault()
      selectStrain(suggestions[activeIndex].name)
    } else if (e.key === "Escape") {
      setShowDropdown(false)
    }
  }

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(e.target as Node) &&
        inputRef.current &&
        !inputRef.current.contains(e.target as Node)
      ) {
        setShowDropdown(false)
      }
    }
    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  return (
    <div className="relative">
      <div className="relative">
        <Input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => handleInputChange(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => suggestions.length > 0 && setShowDropdown(true)}
          placeholder="Search strains (e.g., Blue Dream, OG Kush)"
          disabled={analyzing}
          className="w-full"
          aria-label="Search strains"
          aria-expanded={showDropdown}
          role="combobox"
          aria-autocomplete="list"
        />
        {(loading || analyzing) && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2">
            <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
          </div>
        )}
      </div>

      {showDropdown && suggestions.length > 0 && (
        <div
          ref={dropdownRef}
          className="absolute z-50 w-full mt-1 bg-card border border-border rounded-md shadow-lg max-h-60 overflow-auto"
          role="listbox"
        >
          {suggestions.map((suggestion, index) => (
            <button
              key={suggestion.name}
              type="button"
              className={`w-full text-left px-3 py-2 flex items-center gap-2 text-sm cursor-pointer transition-colors ${
                index === activeIndex
                  ? "bg-accent text-accent-foreground"
                  : "hover:bg-accent/50"
              }`}
              onClick={() => selectStrain(suggestion.name)}
              role="option"
              aria-selected={index === activeIndex}
            >
              <span
                className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${
                  categoryDotColors[suggestion.category] || "bg-gray-400"
                }`}
              />
              <span className="capitalize">{suggestion.name}</span>
              <span className="text-xs text-muted-foreground ml-auto">
                {suggestion.category}
              </span>
            </button>
          ))}
        </div>
      )}

      {analyzing && (
        <p className="text-xs text-muted-foreground mt-2 flex items-center gap-1">
          <Loader2 className="h-3 w-3 animate-spin" />
          Analyzing strain...
        </p>
      )}

      {error && (
        <div className="mt-2 bg-destructive/10 border border-destructive/20 text-destructive px-4 py-3 rounded-md text-sm">
          {error}
        </div>
      )}
    </div>
  )
}
