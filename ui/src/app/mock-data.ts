import { of } from 'rxjs';

export const mockDocuments = [
  {
    id: '1',
    name: 'invoice.pdf',
    categoryId: 'invoice',
    kvp_extraction: { 'Invoice Number': 'INV-12345', 'Date': '2025-10-26', 'Total Amount': '$5,000' },
    kvData: [
      { key: 'Invoice Number', value: 'INV-12345' },
      { key: 'Date', value: '2025-10-26' },
      { key: 'Total Amount', value: '$5,000' },
    ],
  },
  {
    id: '2',
    name: 'receipt.pdf',
    categoryId: 'receipt',
    kvp_extraction: { 'Receipt Number': 'REC-67890', 'Date': '2025-10-25', 'Total Amount': '$100' },
    kvData: [
      { key: 'Receipt Number', value: 'REC-67890' },
      { key: 'Date', value: '2025-10-25' },
      { key: 'Total Amount', value: '$100' },
    ],
  },
  {
    id: '3',
    name: 'contract.pdf',
    categoryId: null,
    kvp_extraction: null,
    kvData: [],
  },
];

export const mockChatService = {
  sendCorrection: (correction: any) => of({ success: true, ...correction }),
  sendGlobalMessage: (message: any) => of({ response: `Mock response to: ${message.message}` }),
  sendCategoryMessage: (message: any) => of({ response: `Mock response in ${message.category} to: ${message.message}` }),
};
