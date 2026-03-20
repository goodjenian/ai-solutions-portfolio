/**
 * Tests for Leads Page.
 *
 * Task #58: Comprehensive Test Suite Update
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import LeadsPage from '../page';
import * as api from '@/lib/api';
import type { LeadWithScore, LeadListResponse, ScoringStatistics } from '@/lib/types';

// Mock the API module
jest.mock('@/lib/api', () => ({
  getLeads: jest.fn(),
  getHighValueLeads: jest.fn(),
  getScoringStatistics: jest.fn(),
  updateLeadStatus: jest.fn(),
  recalculateScores: jest.fn(),
  exportLeads: jest.fn(),
}));

// Mock date-fns
jest.mock('date-fns', () => ({
  formatDistanceToNow: jest.fn(() => '2 hours ago'),
  formatTimeAgo: jest.fn(() => '2 hours ago'),
}));

const mockLeads: LeadWithScore[] = [
  {
    id: 'lead-1',
    visitor_id: 'visitor-1',
    email: 'john@example.com',
    name: 'John Doe',
    status: 'new',
    total_score: 85,
    last_activity_at: new Date().toISOString(),
    created_at: new Date().toISOString(),
    source: 'organic',
    phone: null,
    user_id: null,
    current_score: 85,
    updated_at: new Date().toISOString(),
  },
  {
    id: 'lead-2',
    visitor_id: 'visitor-2',
    email: 'jane@example.com',
    name: 'Jane Smith',
    status: 'contacted',
    total_score: 65,
    last_activity_at: new Date().toISOString(),
    created_at: new Date().toISOString(),
    source: 'referral',
    phone: '+1234567890',
    user_id: 'user-1',
    current_score: 65,
    updated_at: new Date().toISOString(),
  },
  {
    id: 'lead-3',
    visitor_id: 'visitor-3',
    email: 'bob@example.com',
    name: 'Bob Wilson',
    status: 'qualified',
    total_score: 92,
    last_activity_at: new Date().toISOString(),
    created_at: new Date().toISOString(),
    source: 'paid',
    phone: null,
    user_id: null,
    current_score: 92,
    updated_at: new Date().toISOString(),
  },
];

const mockStatistics: ScoringStatistics = {
  total_leads: 100,
  avg_score: 55.5,
  high_value_leads: 15,
  conversion_rate: 0.25,
  converted_leads: 25,
  new_leads_24h: 10,
  score_distribution: {
    high_80_100: 15,
    medium_50_79: 25,
    low_0_49: 60,
  },
  scores_calculated_today: 20,
  model_version: '1.0.0',
  weights: {
    search_activity: 0.3,
    property_views: 0.25,
    engagement: 0.25,
    recency: 0.2,
  },
};

const mockLeadResponse: LeadListResponse = {
  items: mockLeads,
  total: 3,
  page: 1,
  page_size: 50,
  total_pages: 1,
};

describe('LeadsPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (api.getLeads as jest.Mock).mockResolvedValue(mockLeadResponse);
    (api.getHighValueLeads as jest.Mock).mockResolvedValue([mockLeads[2]]);
    (api.getScoringStatistics as jest.Mock).mockResolvedValue(mockStatistics);
  });

  it('renders loading state with skeletons initially', () => {
    render(<LeadsPage />);
    // The page shows Skeleton components while loading
    // Skeleton component renders with animate-pulse class
    const skeletons = document.querySelectorAll('[class*="animate-pulse"]');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('renders leads page title after loading', async () => {
    render(<LeadsPage />);

    await waitFor(() => {
      expect(screen.getByText('Lead Dashboard')).toBeInTheDocument();
    });
  });

  it('renders high value leads section', async () => {
    render(<LeadsPage />);

    await waitFor(() => {
      expect(screen.getByText('High Value Leads')).toBeInTheDocument();
    });
  });

  it('renders statistics cards after loading', async () => {
    render(<LeadsPage />);

    await waitFor(() => {
      expect(screen.getByText('Total Leads')).toBeInTheDocument();
      expect(screen.getByText('Average Score')).toBeInTheDocument();
    });
  });

  it('displays leads in the list', async () => {
    render(<LeadsPage />);

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    expect(screen.getByText('jane@example.com')).toBeInTheDocument();
  });

  it('shows correct status badges', async () => {
    render(<LeadsPage />);

    await waitFor(() => {
      expect(screen.getByText('New')).toBeInTheDocument();
    });
  });

  it('shows score badges', async () => {
    render(<LeadsPage />);

    await waitFor(() => {
      expect(screen.getByText('85')).toBeInTheDocument();
    });
  });

  it('handles API error gracefully', async () => {
    (api.getLeads as jest.Mock).mockRejectedValue(new Error('API Error'));

    render(<LeadsPage />);

    await waitFor(() => {
      // The error component shows "Try Again" button on error
      expect(screen.getByText('Try Again')).toBeInTheDocument();
    });
  });

  it('renders recalculate scores button', async () => {
    render(<LeadsPage />);

    await waitFor(() => {
      expect(screen.getByText('Recalculate Scores')).toBeInTheDocument();
    });
  });

  it('renders export button', async () => {
    render(<LeadsPage />);

    await waitFor(() => {
      expect(screen.getByText('Export')).toBeInTheDocument();
    });
  });

  it('renders search input', async () => {
    render(<LeadsPage />);

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Search leads...')).toBeInTheDocument();
    });
  });

  it('renders tab navigation', async () => {
    render(<LeadsPage />);

    await waitFor(() => {
      expect(screen.getByText('All Leads')).toBeInTheDocument();
      expect(screen.getByText('High Value')).toBeInTheDocument();
      expect(screen.getByText('New')).toBeInTheDocument();
    });
  });
});
