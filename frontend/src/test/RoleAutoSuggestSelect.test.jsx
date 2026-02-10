/**
 * RoleAutoSuggestSelect Component Unit Tests
 * 
 * Tests:
 * 1. Roles loaded and displayed
 * 2. Typing filters suggestions
 * 3. Selecting sets value
 * 4. Unknown role text does not allow selection
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { RoleAutoSuggestSelect } from '@/components/RoleAutoSuggestSelect.jsx';

describe('RoleAutoSuggestSelect', () => {
  const mockRoles = [
    { role_id: 1, role_name: 'Software Engineer' },
    { role_id: 2, role_name: 'Senior Software Engineer' },
    { role_id: 3, role_name: 'Tech Lead' },
    { role_id: 4, role_name: 'Product Manager' },
    { role_id: 5, role_name: 'QA Engineer' }
  ];

  let mockOnChange;

  beforeEach(() => {
    mockOnChange = vi.fn();
  });

  describe('1. Roles Loading and Display', () => {
    it('shows loading placeholder when loading=true', () => {
      render(
        <RoleAutoSuggestSelect
          value={null}
          onChange={mockOnChange}
          roles={[]}
          loading={true}
        />
      );
      
      expect(screen.getByPlaceholderText('Loading roles...')).toBeInTheDocument();
    });

    it('shows select placeholder when roles are loaded', () => {
      render(
        <RoleAutoSuggestSelect
          value={null}
          onChange={mockOnChange}
          roles={mockRoles}
          loading={false}
        />
      );
      
      expect(screen.getByPlaceholderText('Select or type to search...')).toBeInTheDocument();
    });

    it('displays selected role name when value is set', () => {
      render(
        <RoleAutoSuggestSelect
          value={1}
          onChange={mockOnChange}
          roles={mockRoles}
          loading={false}
        />
      );
      
      const input = screen.getByTestId('role-input');
      expect(input.value).toBe('Software Engineer');
    });

    it('shows dropdown with all roles on focus', async () => {
      render(
        <RoleAutoSuggestSelect
          value={null}
          onChange={mockOnChange}
          roles={mockRoles}
          loading={false}
        />
      );
      
      const input = screen.getByTestId('role-input');
      fireEvent.focus(input);
      
      await waitFor(() => {
        expect(screen.getByTestId('role-dropdown')).toBeInTheDocument();
      });
      
      // All roles should be visible
      expect(screen.getByText('Software Engineer')).toBeInTheDocument();
      expect(screen.getByText('Tech Lead')).toBeInTheDocument();
      expect(screen.getByText('Product Manager')).toBeInTheDocument();
    });
  });

  describe('2. Typing Filters Suggestions', () => {
    it('filters roles based on input (case-insensitive)', async () => {
      render(
        <RoleAutoSuggestSelect
          value={null}
          onChange={mockOnChange}
          roles={mockRoles}
          loading={false}
        />
      );
      
      const input = screen.getByTestId('role-input');
      fireEvent.focus(input);
      fireEvent.change(input, { target: { value: 'engineer' } });
      
      await waitFor(() => {
        expect(screen.getByTestId('role-dropdown')).toBeInTheDocument();
      });
      
      // Should show roles containing "engineer"
      expect(screen.getByText('Software Engineer')).toBeInTheDocument();
      expect(screen.getByText('Senior Software Engineer')).toBeInTheDocument();
      expect(screen.getByText('QA Engineer')).toBeInTheDocument();
      
      // Should NOT show roles not containing "engineer"
      expect(screen.queryByText('Tech Lead')).not.toBeInTheDocument();
      expect(screen.queryByText('Product Manager')).not.toBeInTheDocument();
    });

    it('shows no results message when no roles match', async () => {
      render(
        <RoleAutoSuggestSelect
          value={null}
          onChange={mockOnChange}
          roles={mockRoles}
          loading={false}
        />
      );
      
      const input = screen.getByTestId('role-input');
      fireEvent.focus(input);
      fireEvent.change(input, { target: { value: 'xyz123' } });
      
      await waitFor(() => {
        expect(screen.getByTestId('role-no-results')).toBeInTheDocument();
      });
      
      expect(screen.getByText('No matching roles found')).toBeInTheDocument();
    });
  });

  describe('3. Selecting Sets Value', () => {
    it('calls onChange with role_id and role_name when option is clicked', async () => {
      render(
        <RoleAutoSuggestSelect
          value={null}
          onChange={mockOnChange}
          roles={mockRoles}
          loading={false}
        />
      );
      
      const input = screen.getByTestId('role-input');
      fireEvent.focus(input);
      
      await waitFor(() => {
        expect(screen.getByTestId('role-dropdown')).toBeInTheDocument();
      });
      
      fireEvent.click(screen.getByText('Tech Lead'));
      
      expect(mockOnChange).toHaveBeenCalledWith(3, 'Tech Lead');
    });

    it('closes dropdown after selection', async () => {
      render(
        <RoleAutoSuggestSelect
          value={null}
          onChange={mockOnChange}
          roles={mockRoles}
          loading={false}
        />
      );
      
      const input = screen.getByTestId('role-input');
      fireEvent.focus(input);
      
      await waitFor(() => {
        expect(screen.getByTestId('role-dropdown')).toBeInTheDocument();
      });
      
      fireEvent.click(screen.getByText('Tech Lead'));
      
      await waitFor(() => {
        expect(screen.queryByTestId('role-dropdown')).not.toBeInTheDocument();
      });
    });

    it('updates input value after selection', async () => {
      render(
        <RoleAutoSuggestSelect
          value={null}
          onChange={mockOnChange}
          roles={mockRoles}
          loading={false}
        />
      );
      
      const input = screen.getByTestId('role-input');
      fireEvent.focus(input);
      
      await waitFor(() => {
        expect(screen.getByTestId('role-dropdown')).toBeInTheDocument();
      });
      
      fireEvent.click(screen.getByText('Product Manager'));
      
      expect(input.value).toBe('Product Manager');
    });
  });

  describe('4. Keyboard Navigation', () => {
    it('opens dropdown on ArrowDown key', async () => {
      render(
        <RoleAutoSuggestSelect
          value={null}
          onChange={mockOnChange}
          roles={mockRoles}
          loading={false}
        />
      );
      
      const input = screen.getByTestId('role-input');
      fireEvent.keyDown(input, { key: 'ArrowDown' });
      
      await waitFor(() => {
        expect(screen.getByTestId('role-dropdown')).toBeInTheDocument();
      });
    });

    it('closes dropdown on Escape key', async () => {
      render(
        <RoleAutoSuggestSelect
          value={null}
          onChange={mockOnChange}
          roles={mockRoles}
          loading={false}
        />
      );
      
      const input = screen.getByTestId('role-input');
      fireEvent.focus(input);
      
      await waitFor(() => {
        expect(screen.getByTestId('role-dropdown')).toBeInTheDocument();
      });
      
      fireEvent.keyDown(input, { key: 'Escape' });
      
      await waitFor(() => {
        expect(screen.queryByTestId('role-dropdown')).not.toBeInTheDocument();
      });
    });
  });

  describe('5. Disabled State', () => {
    it('disables input when disabled=true', () => {
      render(
        <RoleAutoSuggestSelect
          value={null}
          onChange={mockOnChange}
          roles={mockRoles}
          loading={false}
          disabled={true}
        />
      );
      
      const input = screen.getByTestId('role-input');
      expect(input).toBeDisabled();
    });
  });
});
