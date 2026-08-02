'use client';

import { useMobileNav } from '@/providers/MobileNavProvider';
import { useAuth } from '@/providers/AuthProvider';

export default function Navbar() {
  const { isOpen, toggle } = useMobileNav();
  const { user, logout } = useAuth();

  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
      <div className="flex items-center gap-4">
        <button
          type="button"
          role="button"
          tabIndex={0}
          onClick={toggle}
          aria-expanded={isOpen}
          aria-controls="mobile-sidebar"
          aria-label={isOpen ? 'Close navigation menu' : 'Open navigation menu'}
          className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg md:hidden focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
        >
          {isOpen ? (
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-6 w-6"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          ) : (
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-6 w-6"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 6h16M4 12h16M4 18h16"
              />
            </svg>
          )}
        </button>
        <h2 className="text-lg font-semibold text-gray-900">Dashboard</h2>
      </div>
      <div className="flex items-center gap-4">
        {user && (
          <div className="flex items-center gap-3">
            <span className="text-sm font-medium text-gray-700 hidden sm:block">
              {user.full_name || user.email}
            </span>
            <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-white font-medium shadow-sm">
              {(user.full_name || user.email || 'MM').substring(0, 2).toUpperCase()}
            </div>
            <button
              onClick={logout}
              className="text-sm text-gray-500 hover:text-gray-700 px-2 py-1 rounded hover:bg-gray-100 transition-colors"
            >
              Log out
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
