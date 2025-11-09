'use client'

import { Receipt } from '@/types'
import { format } from 'date-fns'
import { FileText, Calendar, DollarSign } from 'lucide-react'

interface ReceiptListProps {
  receipts: Receipt[]
}

export default function ReceiptList({ receipts }: ReceiptListProps) {
  if (receipts.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-8 text-center">
        <FileText className="mx-auto h-12 w-12 text-gray-400 mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No receipts yet</h3>
        <p className="text-gray-600">Upload your first receipt to get started!</p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="px-6 py-4 border-b border-gray-200">
        <h2 className="text-xl font-bold text-gray-900">Recent Receipts</h2>
      </div>
      <div className="divide-y divide-gray-200">
        {receipts.map((receipt) => (
          <div
            key={receipt.id}
            className="px-6 py-4 hover:bg-gray-50 transition cursor-pointer"
          >
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-3">
                  <div className="flex-shrink-0">
                    <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                      <FileText className="h-5 w-5 text-blue-600" />
                    </div>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {receipt.merchantName}
                    </p>
                    <div className="flex items-center space-x-4 mt-1">
                      <div className="flex items-center text-xs text-gray-500">
                        <Calendar className="h-3 w-3 mr-1" />
                        {receipt.date ? format(new Date(receipt.date), 'MMM dd, yyyy') : 'N/A'}
                      </div>
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                        {receipt.category}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
              <div className="ml-4 flex-shrink-0">
                <div className="flex items-center text-lg font-semibold text-gray-900">
                  <DollarSign className="h-5 w-5 text-gray-400" />
                  {receipt.totalAmount.toFixed(2)}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
