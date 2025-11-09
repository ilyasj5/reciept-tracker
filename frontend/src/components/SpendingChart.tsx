'use client'

import { useMemo } from 'react'
import { Receipt, CategorySpending } from '@/types'
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts'

interface SpendingChartProps {
  receipts: Receipt[]
  detailed?: boolean
}

const COLORS = [
  '#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8',
  '#82CA9D', '#FFC658', '#FF6B9D', '#C084FC', '#A78BFA'
]

export default function SpendingChart({ receipts, detailed = false }: SpendingChartProps) {
  const categoryData = useMemo(() => {
    const categoryMap = new Map<string, CategorySpending>()

    receipts.forEach((receipt) => {
      const existing = categoryMap.get(receipt.category) || {
        category: receipt.category,
        amount: 0,
        percentage: 0,
        transactionCount: 0,
      }

      categoryMap.set(receipt.category, {
        ...existing,
        amount: existing.amount + receipt.totalAmount,
        transactionCount: existing.transactionCount + 1,
      })
    })

    const total = Array.from(categoryMap.values()).reduce((sum, cat) => sum + cat.amount, 0)

    return Array.from(categoryMap.values()).map((cat) => ({
      ...cat,
      percentage: total > 0 ? (cat.amount / total) * 100 : 0,
    }))
  }, [receipts])

  const totalSpending = useMemo(() => {
    return receipts.reduce((sum, receipt) => sum + receipt.totalAmount, 0)
  }, [receipts])

  if (receipts.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Spending by Category</h2>
        <p className="text-gray-600 text-center py-8">No data available yet</p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-bold text-gray-900 mb-4">Spending by Category</h2>

      <div className="mb-6">
        <p className="text-sm text-gray-600 mb-1">Total Spending</p>
        <p className="text-3xl font-bold text-gray-900">${totalSpending.toFixed(2)}</p>
      </div>

      <ResponsiveContainer width="100%" height={250}>
        <PieChart>
          <Pie
            data={categoryData}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ category, percentage }) =>
              percentage > 5 ? `${category} ${percentage.toFixed(0)}%` : ''
            }
            outerRadius={80}
            fill="#8884d8"
            dataKey="amount"
          >
            {categoryData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip
            formatter={(value: number) => `$${value.toFixed(2)}`}
          />
          {detailed && <Legend />}
        </PieChart>
      </ResponsiveContainer>

      {detailed && (
        <div className="mt-6 space-y-3">
          {categoryData.map((cat, index) => (
            <div key={cat.category} className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div
                  className="w-4 h-4 rounded-full"
                  style={{ backgroundColor: COLORS[index % COLORS.length] }}
                />
                <span className="text-sm font-medium text-gray-900">{cat.category}</span>
              </div>
              <div className="text-right">
                <p className="text-sm font-semibold text-gray-900">${cat.amount.toFixed(2)}</p>
                <p className="text-xs text-gray-500">{cat.transactionCount} transactions</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
