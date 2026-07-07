/**
 * COMPONENT TEST TEMPLATE
 *
 * This file demonstrates the structure for testing React components.
 * Copy this template and adapt it to your component.
 *
 * Testing Checklist:
 * ✓ Component renders without crashing
 * ✓ Props are correctly applied
 * ✓ User interactions trigger callbacks
 * ✓ Conditional rendering works
 * ✓ Loading/error states display correctly
 * ✓ Accessibility features (aria-labels, roles, etc.)
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

/**
 * Example: Testing a simple Button component
 */
describe('Button Component', () => {
  it('renders button with text', () => {
    const Button = ({ label, onClick }: { label: string; onClick: () => void }) => (
      <button onClick={onClick}>{label}</button>
    );

    render(<Button label="Click me" onClick={jest.fn()} />);
    expect(screen.getByRole('button', { name: /click me/i })).toBeInTheDocument();
  });

  it('calls onClick handler when clicked', async () => {
    const handleClick = jest.fn();
    const Button = ({ label, onClick }: { label: string; onClick: () => void }) => (
      <button onClick={onClick}>{label}</button>
    );

    render(<Button label="Click me" onClick={handleClick} />);
    await userEvent.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('disables button when disabled prop is true', () => {
    const Button = ({
      label,
      disabled,
      onClick,
    }: {
      label: string;
      disabled?: boolean;
      onClick: () => void;
    }) => (
      <button onClick={onClick} disabled={disabled}>
        {label}
      </button>
    );

    render(<Button label="Click me" disabled={true} onClick={jest.fn()} />);
    expect(screen.getByRole('button')).toBeDisabled();
  });
});

/**
 * Example: Testing a component with loading/error states
 */
describe('DataFetching Component', () => {
  const DataFetcher = ({
    isLoading,
    error,
    data,
  }: {
    isLoading: boolean;
    error: string | null;
    data: any;
  }) => {
    if (isLoading) return <div>Loading...</div>;
    if (error) return <div role="alert">Error: {error}</div>;
    return <div>{data?.name || 'No data'}</div>;
  };

  it('shows loading state', () => {
    render(<DataFetcher isLoading={true} error={null} data={null} />);
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('shows error state', () => {
    render(<DataFetcher isLoading={false} error="Failed to load" data={null} />);
    expect(screen.getByRole('alert')).toHaveTextContent(/failed to load/i);
  });

  it('displays data when loaded', () => {
    const mockData = { name: 'John Doe' };
    render(
      <DataFetcher
        isLoading={false}
        error={null}
        data={mockData}
      />
    );
    expect(screen.getByText('John Doe')).toBeInTheDocument();
  });
});

/**
 * Example: Testing a form component
 */
describe('Form Component', () => {
  const Form = ({ onSubmit }: { onSubmit: (data: any) => void }) => {
    const [email, setEmail] = React.useState('');
    const handleSubmit = (e: React.FormEvent) => {
      e.preventDefault();
      onSubmit({ email });
    };

    return (
      <form onSubmit={handleSubmit}>
        <label htmlFor="email">Email</label>
        <input
          id="email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <button type="submit">Submit</button>
      </form>
    );
  };

  it('submits form with email value', async () => {
    const handleSubmit = jest.fn();
    render(<Form onSubmit={handleSubmit} />);

    const emailInput = screen.getByLabelText(/email/i);
    await userEvent.type(emailInput, 'test@example.com');

    await userEvent.click(screen.getByRole('button', { name: /submit/i }));

    expect(handleSubmit).toHaveBeenCalledWith({
      email: 'test@example.com',
    });
  });

  it('requires email input', () => {
    render(<Form onSubmit={jest.fn()} />);
    const emailInput = screen.getByLabelText(/email/i) as HTMLInputElement;
    expect(emailInput.required).toBe(true);
  });
});

/**
 * Example: Testing a list/table component
 */
describe('List Component', () => {
  const List = ({ items }: { items: Array<{ id: string; name: string }> }) => (
    <ul>
      {items.map((item) => (
        <li key={item.id}>{item.name}</li>
      ))}
    </ul>
  );

  it('renders all list items', () => {
    const mockItems = [
      { id: '1', name: 'Item 1' },
      { id: '2', name: 'Item 2' },
      { id: '3', name: 'Item 3' },
    ];

    render(<List items={mockItems} />);

    mockItems.forEach((item) => {
      expect(screen.getByText(item.name)).toBeInTheDocument();
    });
  });

  it('shows empty state when no items', () => {
    const List = ({ items }: { items: Array<{ id: string; name: string }> }) => (
      <>
        {items.length === 0 ? (
          <p>No items found</p>
        ) : (
          <ul>
            {items.map((item) => (
              <li key={item.id}>{item.name}</li>
            ))}
          </ul>
        )}
      </>
    );

    render(<List items={[]} />);
    expect(screen.getByText(/no items found/i)).toBeInTheDocument();
  });
});

/**
 * Example: Testing a component with async operations
 */
describe('AsyncComponent', () => {
  const AsyncComponent = ({ fetchData }: { fetchData: () => Promise<string> }) => {
    const [data, setData] = React.useState<string | null>(null);
    const [loading, setLoading] = React.useState(false);

    const handleLoad = async () => {
      setLoading(true);
      try {
        const result = await fetchData();
        setData(result);
      } finally {
        setLoading(false);
      }
    };

    return (
      <div>
        <button onClick={handleLoad}>Load Data</button>
        {loading && <p>Loading...</p>}
        {data && <p>{data}</p>}
      </div>
    );
  };

  it('handles async data loading', async () => {
    const mockFetchData = jest.fn().mockResolvedValue('Test Data');
    render(<AsyncComponent fetchData={mockFetchData} />);

    await userEvent.click(screen.getByRole('button', { name: /load data/i }));

    await waitFor(() => {
      expect(screen.getByText('Test Data')).toBeInTheDocument();
    });

    expect(mockFetchData).toHaveBeenCalled();
  });

  it('shows loading state during fetch', async () => {
    const mockFetchData = jest.fn(
      () => new Promise((resolve) => setTimeout(() => resolve('Data'), 100))
    );

    render(<AsyncComponent fetchData={mockFetchData} />);

    await userEvent.click(screen.getByRole('button'));

    expect(screen.getByText('Loading...')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
    });
  });

  it('handles fetch errors', async () => {
    const mockError = new Error('Fetch failed');
    const mockFetchData = jest.fn().mockRejectedValue(mockError);

    const ComponentWithErrorHandling = () => {
      const [error, setError] = React.useState<string | null>(null);

      const handleLoad = async () => {
        try {
          await mockFetchData();
        } catch (err) {
          setError((err as Error).message);
        }
      };

      return (
        <div>
          <button onClick={handleLoad}>Load Data</button>
          {error && <p role="alert">{error}</p>}
        </div>
      );
    };

    render(<ComponentWithErrorHandling />);
    await userEvent.click(screen.getByRole('button'));

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent('Fetch failed');
    });
  });
});

/**
 * Key Testing Patterns:
 *
 * 1. Render Test:
 *    - Ensure component mounts without errors
 *    - Check that key elements are present
 *
 * 2. Props Test:
 *    - Verify that props are applied correctly
 *    - Test optional vs required props
 *    - Test different prop combinations
 *
 * 3. Interaction Test:
 *    - Simulate user clicks, typing, etc.
 *    - Use userEvent instead of fireEvent for better simulation
 *    - Verify callbacks are called correctly
 *
 * 4. State Test:
 *    - Test conditional rendering based on state
 *    - Verify state updates trigger re-renders
 *
 * 5. Async Test:
 *    - Use waitFor() for async operations
 *    - Test loading and error states
 *    - Verify data is displayed after loading
 *
 * 6. Accessibility Test:
 *    - Use semantic roles (button, link, heading, etc.)
 *    - Test that form labels are connected to inputs
 *    - Verify aria-labels where needed
 */
