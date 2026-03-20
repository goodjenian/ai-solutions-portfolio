/**
 * Tests for Documents Page.
 *
 * Task #58: Comprehensive Test Suite Update
 */

import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import DocumentsPage from '../page';
import * as api from '@/lib/api';
import type { Document, DocumentListResponse, ExpiringDocumentsResponse } from '@/lib/types';

// Mock the API module
jest.mock('@/lib/api', () => ({
  getDocuments: jest.fn(),
  getExpiringDocuments: jest.fn(),
}));

// Mock the document components
jest.mock('@/components/documents/document-upload', () => ({
  DocumentUpload: ({
    onUploadSuccess,
    onCancel,
  }: {
    onUploadSuccess: () => void;
    onCancel: () => void;
  }) => (
    <div data-testid="document-upload">
      <button onClick={onUploadSuccess} data-testid="upload-success-btn">
        Upload Success
      </button>
      <button onClick={onCancel} data-testid="upload-cancel-btn">
        Cancel
      </button>
    </div>
  ),
}));

jest.mock('@/components/documents/document-list', () => ({
  DocumentList: ({
    documents,
    onDocumentDeleted,
    onDocumentUpdated,
  }: {
    documents: Document[];
    onDocumentDeleted: (id: string) => void;
    onDocumentUpdated: (doc: Document) => void;
  }) => (
    <div data-testid="document-list">
      {documents.map((doc) => (
        <div key={doc.id} data-testid={`document-${doc.id}`}>
          <span>{doc.original_filename}</span>
          <button onClick={() => onDocumentDeleted(doc.id)}>Delete</button>
          <button onClick={() => onDocumentUpdated({ ...doc, description: 'Updated' })}>
            Update
          </button>
        </div>
      ))}
    </div>
  ),
}));

const mockDocuments: Document[] = [
  {
    id: 'doc-1',
    user_id: 'user-1',
    original_filename: 'contract.pdf',
    filename: 'unique-contract.pdf',
    file_type: 'application/pdf',
    file_size: 102400,
    category: 'contract',
    tags: ['important'],
    description: 'Sales contract',
    storage_path: '/storage/doc-1.pdf',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    ocr_status: 'completed',
    property_id: null,
    expiry_date: null,
  },
  {
    id: 'doc-2',
    user_id: 'user-1',
    original_filename: 'floorplan.jpg',
    filename: 'unique-floorplan.jpg',
    file_type: 'image/jpeg',
    file_size: 204800,
    category: 'floorplan',
    tags: [],
    description: 'Floor plan',
    storage_path: '/storage/doc-2.jpg',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    ocr_status: 'pending',
    property_id: 'prop-1',
    expiry_date: null,
  },
];

const mockDocumentResponse: DocumentListResponse = {
  items: mockDocuments,
  total: 2,
  page: 1,
  page_size: 20,
  total_pages: 1,
};

const mockExpiringResponse: ExpiringDocumentsResponse = {
  items: [
    {
      ...mockDocuments[0],
      expiry_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
    },
  ],
  total: 1,
  days_ahead: 30,
};

describe('DocumentsPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (api.getDocuments as jest.Mock).mockResolvedValue(mockDocumentResponse);
    (api.getExpiringDocuments as jest.Mock).mockResolvedValue(mockExpiringResponse);
  });

  it('renders loading state initially', () => {
    render(<DocumentsPage />);
    expect(screen.getByText('Loading documents...')).toBeInTheDocument();
  });

  it('renders documents page title after loading', async () => {
    render(<DocumentsPage />);

    await waitFor(() => {
      expect(screen.getByText('Documents')).toBeInTheDocument();
    });
  });

  it('renders upload button', async () => {
    render(<DocumentsPage />);

    await waitFor(() => {
      expect(screen.getByText('Upload Document')).toBeInTheDocument();
    });
  });

  it('renders refresh button', async () => {
    render(<DocumentsPage />);

    await waitFor(() => {
      expect(screen.getByText('Refresh')).toBeInTheDocument();
    });
  });

  it('displays documents in the list', async () => {
    render(<DocumentsPage />);

    await waitFor(() => {
      // Document filename appears in list (and possibly in expiry alert)
      const contractElements = screen.getAllByText('contract.pdf');
      expect(contractElements.length).toBeGreaterThan(0);
    });

    const floorplanElements = screen.getAllByText('floorplan.jpg');
    expect(floorplanElements.length).toBeGreaterThan(0);
  });

  it('shows expiring documents alert', async () => {
    render(<DocumentsPage />);

    await waitFor(() => {
      expect(screen.getByText(/expiring soon/i)).toBeInTheDocument();
    });
  });

  it('opens upload modal when upload button is clicked', async () => {
    render(<DocumentsPage />);

    await waitFor(() => {
      expect(screen.getByText('Upload Document')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Upload Document'));

    await waitFor(() => {
      expect(screen.getByTestId('document-upload')).toBeInTheDocument();
    });
  });

  it('closes upload modal on cancel', async () => {
    render(<DocumentsPage />);

    await waitFor(() => {
      expect(screen.getByText('Upload Document')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Upload Document'));

    await waitFor(() => {
      expect(screen.getByTestId('document-upload')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId('upload-cancel-btn'));

    await waitFor(() => {
      expect(screen.queryByTestId('document-upload')).not.toBeInTheDocument();
    });
  });

  it('handles API error gracefully', async () => {
    (api.getDocuments as jest.Mock).mockRejectedValue(new Error('API Error'));

    render(<DocumentsPage />);

    await waitFor(() => {
      expect(screen.getByText(/Failed to load documents/i)).toBeInTheDocument();
    });
  });

  it('shows empty state when no documents', async () => {
    (api.getDocuments as jest.Mock).mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 20,
      total_pages: 1,
    });

    render(<DocumentsPage />);

    await waitFor(() => {
      expect(screen.getByText('No documents yet')).toBeInTheDocument();
    });
  });

  it('removes document from list after deletion', async () => {
    render(<DocumentsPage />);

    await waitFor(() => {
      // Check document is in the list via test id
      expect(screen.getByTestId('document-doc-1')).toBeInTheDocument();
    });

    // Click delete button for first document
    fireEvent.click(screen.getAllByText('Delete')[0]);

    await waitFor(() => {
      // Document should be removed from the list
      expect(screen.queryByTestId('document-doc-1')).not.toBeInTheDocument();
    });
  });
});
