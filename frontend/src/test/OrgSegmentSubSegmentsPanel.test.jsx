/**
 * Unit tests for OrgSegmentSubSegmentsPanel component
 * 
 * Tests the inline add sub-segment functionality including:
 * - Successful add
 * - Duplicate error handling (409 response)
 * - Error message display and clearing
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import OrgSegmentSubSegmentsPanel from '@/pages/MasterData/components/OrgSegmentSubSegmentsPanel';

describe('OrgSegmentSubSegmentsPanel', () => {
  const mockSubSegments = [
    { id: 'subseg-1', name: 'Existing SubSegment 1' },
    { id: 'subseg-2', name: 'Existing SubSegment 2' },
  ];

  let mockCreateSubSegment;
  let mockEditSubSegment;
  let mockDeleteSubSegment;

  beforeEach(() => {
    mockCreateSubSegment = vi.fn();
    mockEditSubSegment = vi.fn();
    mockDeleteSubSegment = vi.fn();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('renders sub-segments table with existing items', () => {
    render(
      <OrgSegmentSubSegmentsPanel
        subSegments={mockSubSegments}
        segmentName="Test Segment"
        onCreateSubSegment={mockCreateSubSegment}
        onEditSubSegment={mockEditSubSegment}
        onDeleteSubSegment={mockDeleteSubSegment}
      />
    );

    expect(screen.getByText('Existing SubSegment 1')).toBeInTheDocument();
    expect(screen.getByText('Existing SubSegment 2')).toBeInTheDocument();
  });

  it('shows inline add row when "+ Add Sub-segment" button is clicked', () => {
    render(
      <OrgSegmentSubSegmentsPanel
        subSegments={mockSubSegments}
        segmentName="Test Segment"
        onCreateSubSegment={mockCreateSubSegment}
        onEditSubSegment={mockEditSubSegment}
        onDeleteSubSegment={mockDeleteSubSegment}
      />
    );

    const addButton = screen.getByRole('button', { name: /\+ Add Sub-segment/i });
    fireEvent.click(addButton);

    expect(screen.getByPlaceholderText('Enter sub-segment name')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Save/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Cancel/i })).toBeInTheDocument();
  });

  it('calls onCreateSubSegment and exits add mode on successful save', async () => {
    mockCreateSubSegment.mockResolvedValue({});

    render(
      <OrgSegmentSubSegmentsPanel
        subSegments={mockSubSegments}
        segmentName="Test Segment"
        onCreateSubSegment={mockCreateSubSegment}
        onEditSubSegment={mockEditSubSegment}
        onDeleteSubSegment={mockDeleteSubSegment}
      />
    );

    // Open add mode
    const addButton = screen.getByRole('button', { name: /\+ Add Sub-segment/i });
    fireEvent.click(addButton);

    // Enter name
    const input = screen.getByPlaceholderText('Enter sub-segment name');
    fireEvent.change(input, { target: { value: 'New SubSegment' } });

    // Click save
    const saveButton = screen.getByRole('button', { name: /Save/i });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(mockCreateSubSegment).toHaveBeenCalledWith('New SubSegment');
    });

    // Add mode should be closed
    await waitFor(() => {
      expect(screen.queryByPlaceholderText('Enter sub-segment name')).not.toBeInTheDocument();
    });
  });

  it('shows inline error message when API returns 409 duplicate error', async () => {
    const duplicateError = new Error("'ADT' sub-segment already exists in Segment 'DTS'.");
    duplicateError.status = 409;
    mockCreateSubSegment.mockRejectedValue(duplicateError);

    render(
      <OrgSegmentSubSegmentsPanel
        subSegments={mockSubSegments}
        segmentName="DTS"
        onCreateSubSegment={mockCreateSubSegment}
        onEditSubSegment={mockEditSubSegment}
        onDeleteSubSegment={mockDeleteSubSegment}
      />
    );

    // Open add mode
    const addButton = screen.getByRole('button', { name: /\+ Add Sub-segment/i });
    fireEvent.click(addButton);

    // Enter duplicate name
    const input = screen.getByPlaceholderText('Enter sub-segment name');
    fireEvent.change(input, { target: { value: 'ADT' } });

    // Click save
    const saveButton = screen.getByRole('button', { name: /Save/i });
    fireEvent.click(saveButton);

    // Error message should be displayed
    await waitFor(() => {
      expect(screen.getByText("'ADT' sub-segment already exists in Segment 'DTS'.")).toBeInTheDocument();
    });

    // Add row should still be visible (not closed)
    expect(screen.getByPlaceholderText('Enter sub-segment name')).toBeInTheDocument();
  });

  it('clears error message when user edits the input', async () => {
    const duplicateError = new Error("'ADT' sub-segment already exists in Segment 'DTS'.");
    duplicateError.status = 409;
    mockCreateSubSegment.mockRejectedValue(duplicateError);

    render(
      <OrgSegmentSubSegmentsPanel
        subSegments={mockSubSegments}
        segmentName="DTS"
        onCreateSubSegment={mockCreateSubSegment}
        onEditSubSegment={mockEditSubSegment}
        onDeleteSubSegment={mockDeleteSubSegment}
      />
    );

    // Open add mode and trigger error
    const addButton = screen.getByRole('button', { name: /\+ Add Sub-segment/i });
    fireEvent.click(addButton);

    const input = screen.getByPlaceholderText('Enter sub-segment name');
    fireEvent.change(input, { target: { value: 'ADT' } });

    const saveButton = screen.getByRole('button', { name: /Save/i });
    fireEvent.click(saveButton);

    // Wait for error to appear
    await waitFor(() => {
      expect(screen.getByText("'ADT' sub-segment already exists in Segment 'DTS'.")).toBeInTheDocument();
    });

    // Edit the input
    fireEvent.change(input, { target: { value: 'ADT-New' } });

    // Error message should be cleared
    await waitFor(() => {
      expect(screen.queryByText("'ADT' sub-segment already exists in Segment 'DTS'.")).not.toBeInTheDocument();
    });
  });

  it('clears error message when cancel is clicked', async () => {
    const duplicateError = new Error("'ADT' sub-segment already exists in Segment 'DTS'.");
    duplicateError.status = 409;
    mockCreateSubSegment.mockRejectedValue(duplicateError);

    render(
      <OrgSegmentSubSegmentsPanel
        subSegments={mockSubSegments}
        segmentName="DTS"
        onCreateSubSegment={mockCreateSubSegment}
        onEditSubSegment={mockEditSubSegment}
        onDeleteSubSegment={mockDeleteSubSegment}
      />
    );

    // Open add mode and trigger error
    const addButton = screen.getByRole('button', { name: /\+ Add Sub-segment/i });
    fireEvent.click(addButton);

    const input = screen.getByPlaceholderText('Enter sub-segment name');
    fireEvent.change(input, { target: { value: 'ADT' } });

    const saveButton = screen.getByRole('button', { name: /Save/i });
    fireEvent.click(saveButton);

    // Wait for error to appear
    await waitFor(() => {
      expect(screen.getByText("'ADT' sub-segment already exists in Segment 'DTS'.")).toBeInTheDocument();
    });

    // Click cancel
    const cancelButton = screen.getByRole('button', { name: /Cancel/i });
    fireEvent.click(cancelButton);

    // Add row should be closed
    await waitFor(() => {
      expect(screen.queryByPlaceholderText('Enter sub-segment name')).not.toBeInTheDocument();
    });
  });

  it('shows error message for non-409 errors', async () => {
    const genericError = new Error('Network error');
    genericError.status = 500;
    mockCreateSubSegment.mockRejectedValue(genericError);

    render(
      <OrgSegmentSubSegmentsPanel
        subSegments={mockSubSegments}
        segmentName="Test Segment"
        onCreateSubSegment={mockCreateSubSegment}
        onEditSubSegment={mockEditSubSegment}
        onDeleteSubSegment={mockDeleteSubSegment}
      />
    );

    // Open add mode
    const addButton = screen.getByRole('button', { name: /\+ Add Sub-segment/i });
    fireEvent.click(addButton);

    const input = screen.getByPlaceholderText('Enter sub-segment name');
    fireEvent.change(input, { target: { value: 'Test' } });

    const saveButton = screen.getByRole('button', { name: /Save/i });
    fireEvent.click(saveButton);

    // Error message should be displayed
    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeInTheDocument();
    });

    // Add row should still be visible
    expect(screen.getByPlaceholderText('Enter sub-segment name')).toBeInTheDocument();
  });
});
