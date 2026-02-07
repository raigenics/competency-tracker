import { useState, useEffect } from 'react';
import { X, Loader2, Eye, EyeOff } from 'lucide-react';
import { rbacAdminApi } from '../../../services/api/rbacAdminApi.js';

/**
 * Add User Modal Component
 * 
 * Modal form for creating a new user account.
 * Step 1: Create user with login credentials.
 * Step 2: Assign roles (done in Manage Access modal after creation).
 */
const AddUserModal = ({ onClose, onUserCreated }) => {
  // Form state
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    password: '',
    status: 'active',
    link_to_employee_id: ''
  });

  const [showPassword, setShowPassword] = useState(false);
  const [linkEmployee, setLinkEmployee] = useState(false);
  const [employees, setEmployees] = useState([]);
  const [loadingEmployees, setLoadingEmployees] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [errors, setErrors] = useState({});

  // Load employees when link employee checkbox is checked
  useEffect(() => {
    if (linkEmployee && employees.length === 0) {
      loadEmployees();
    }
  }, [linkEmployee]);

  /**
   * Load employee list for dropdown
   */
  const loadEmployees = async () => {
    setLoadingEmployees(true);
    try {
      const data = await rbacAdminApi.searchEmployees();
      setEmployees(data || []);
    } catch (error) {
      console.error('Failed to load employees:', error);
      alert('Failed to load employee list');
    } finally {
      setLoadingEmployees(false);
    }
  };

  /**
   * Handle form field changes
   */
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    // Clear error for this field
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: null }));
    }
  };

  /**
   * Validate form
   */
  const validate = () => {
    const newErrors = {};

    if (!formData.full_name.trim()) {
      newErrors.full_name = 'Full name is required';
    }

    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Invalid email address';
    }

    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    }

    if (linkEmployee && !formData.link_to_employee_id) {
      newErrors.link_to_employee_id = 'Please select an employee';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  /**
   * Handle form submission
   */
  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validate()) {
      return;
    }

    setSubmitting(true);
    try {
      // Prepare data for API
      const userData = {
        full_name: formData.full_name.trim(),
        email: formData.email.trim().toLowerCase(),
        password: formData.password,
        status: formData.status
      };

      // Add employee link if checkbox is checked
      if (linkEmployee && formData.link_to_employee_id) {
        userData.link_to_employee_id = parseInt(formData.link_to_employee_id);
      }

      const createdUser = await rbacAdminApi.createUser(userData);
      
      onUserCreated(createdUser);
    } catch (error) {
      console.error('Failed to create user:', error);
      
      // Parse error message
      const errorMessage = error.response?.data?.detail || error.message || 'Unknown error';
      
      // Check for specific validation errors
      if (errorMessage.includes('email') && errorMessage.includes('already')) {
        setErrors({ email: 'This email is already registered' });
      } else if (errorMessage.includes('employee') && errorMessage.includes('linked')) {
        setErrors({ link_to_employee_id: 'This employee is already linked to another user' });
      } else {
        alert(`Failed to create user: ${errorMessage}`);
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="rbac-modal-overlay">
      <div className="rbac-modal" style={{ maxWidth: '500px' }}>
        {/* Modal Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Add New User</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
            disabled={submitting}
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Modal Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Info Box */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <p className="text-sm text-blue-800">
              <strong>Step 1:</strong> Create user login identity. Role assignment happens in Step 2.
            </p>
          </div>

          {/* Full Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Full Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              name="full_name"
              value={formData.full_name}
              onChange={handleChange}
              placeholder="e.g., John Doe"
              disabled={submitting}
              className={`block w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 ${
                errors.full_name ? 'border-red-300' : 'border-gray-300'
              }`}
            />
            {errors.full_name && (
              <p className="mt-1 text-sm text-red-600">{errors.full_name}</p>
            )}
          </div>

          {/* Email */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Email <span className="text-red-500">*</span>
            </label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="e.g., john.doe@company.com"
              disabled={submitting}
              className={`block w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 ${
                errors.email ? 'border-red-300' : 'border-gray-300'
              }`}
            />
            <p className="mt-1 text-xs text-gray-500">This will be used for login</p>
            {errors.email && (
              <p className="mt-1 text-sm text-red-600">{errors.email}</p>
            )}
          </div>

          {/* Password */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Initial Password <span className="text-red-500">*</span>
            </label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                name="password"
                value={formData.password}
                onChange={handleChange}
                placeholder="Min 8 characters"
                disabled={submitting}
                className={`block w-full px-3 py-2 pr-10 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 ${
                  errors.password ? 'border-red-300' : 'border-gray-300'
                }`}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600"
              >
                {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>
            <p className="mt-1 text-xs text-gray-500">User can change this after first login</p>
            {errors.password && (
              <p className="mt-1 text-sm text-red-600">{errors.password}</p>
            )}
          </div>

          {/* Status */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Status <span className="text-red-500">*</span>
            </label>
            <select
              name="status"
              value={formData.status}
              onChange={handleChange}
              disabled={submitting}
              className="block w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
          </div>

          {/* Link Employee Checkbox */}
          <div>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={linkEmployee}
                onChange={(e) => setLinkEmployee(e.target.checked)}
                disabled={submitting}
                className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
              />
              <span className="text-sm font-medium text-gray-700">
                Link to existing employee record
              </span>
            </label>
          </div>

          {/* Employee Select (conditional) */}
          {linkEmployee && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Select Employee <span className="text-red-500">*</span>
              </label>
              <select
                name="link_to_employee_id"
                value={formData.link_to_employee_id}
                onChange={handleChange}
                disabled={submitting || loadingEmployees}
                className={`block w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 ${
                  errors.link_to_employee_id ? 'border-red-300' : 'border-gray-300'
                }`}
              >
                <option value="">
                  {loadingEmployees ? 'Loading employees...' : 'Select employee...'}
                </option>
                {employees.map((emp) => (
                  <option key={emp.employee_id} value={emp.employee_id}>
                    {emp.zid} - {emp.employee_name}
                  </option>
                ))}
              </select>
              {errors.link_to_employee_id && (
                <p className="mt-1 text-sm text-red-600">{errors.link_to_employee_id}</p>
              )}
            </div>
          )}
        </form>

        {/* Modal Footer */}
        <div className="flex gap-3 justify-end p-6 border-t border-gray-200 bg-gray-50">
          <button
            type="button"
            onClick={onClose}
            disabled={submitting}
            className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Cancel
          </button>
          <button
            type="submit"
            onClick={handleSubmit}
            disabled={submitting}
            className="inline-flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {submitting && <Loader2 className="w-4 h-4 animate-spin" />}
            Create User & Assign Roles
          </button>
        </div>
      </div>
    </div>
  );
};

export default AddUserModal;
