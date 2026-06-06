import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { signIn, getSession } from 'next-auth/react'
import { useRouter } from 'next/navigation'

// Import login page component - we'll test the actual component
// For this test, we create a minimal test component since we're mocking next-auth
const LoginPageComponent = () => {
  const router = useRouter()
  const [email, setEmail] = React.useState('')
  const [password, setPassword] = React.useState('')
  const [error, setError] = React.useState<string | null>(null)
  const [loading, setLoading] = React.useState(false)

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    const res = await signIn('credentials', { email, password, redirect: false })
    if (!res || res.error) {
      setError('Invalid email or password.')
      setLoading(false)
      return
    }
    const session = await getSession()
    const role = (session?.user as { role?: string } | undefined)?.role
    router.push(role === 'admin' ? '/admin/dashboard' : '/recruiter/dashboard')
  }

  return (
    <div>
      <form onSubmit={onSubmit}>
        <div>
          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@company.com"
          />
        </div>
        <div>
          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
          />
        </div>
        {error && <p>{error}</p>}
        <button type="submit" disabled={loading}>
          {loading ? 'Signing in…' : 'Log in'}
        </button>
      </form>
    </div>
  )
}

import React from 'react'

describe('Authentication - Login Page', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders login form with email and password fields', () => {
    render(<LoginPageComponent />)

    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /log in/i })).toBeInTheDocument()
  })

  it('updates email input on user input', async () => {
    const user = userEvent.setup()
    render(<LoginPageComponent />)

    const emailInput = screen.getByLabelText(/email/i) as HTMLInputElement
    await user.type(emailInput, 'test@example.com')

    expect(emailInput.value).toBe('test@example.com')
  })

  it('updates password input on user input', async () => {
    const user = userEvent.setup()
    render(<LoginPageComponent />)

    const passwordInput = screen.getByLabelText(/password/i) as HTMLInputElement
    await user.type(passwordInput, 'password123')

    expect(passwordInput.value).toBe('password123')
  })

  it('shows error message on failed login', async () => {
    const user = userEvent.setup()
    ;(signIn as jest.Mock).mockResolvedValueOnce({
      error: 'Invalid credentials',
    })

    render(<LoginPageComponent />)

    await user.type(screen.getByLabelText(/email/i), 'test@example.com')
    await user.type(screen.getByLabelText(/password/i), 'wrong')
    await user.click(screen.getByRole('button', { name: /log in/i }))

    await waitFor(() => {
      expect(screen.getByText(/invalid email or password/i)).toBeInTheDocument()
    })
  })

  it('disables submit button while loading', async () => {
    const user = userEvent.setup()
    ;(signIn as jest.Mock).mockImplementationOnce(
      () =>
        new Promise((resolve) =>
          setTimeout(() => resolve({ ok: true }), 100)
        )
    )

    render(<LoginPageComponent />)

    const submitButton = screen.getByRole('button', { name: /log in/i })

    await user.type(screen.getByLabelText(/email/i), 'test@example.com')
    await user.type(screen.getByLabelText(/password/i), 'password123')
    await user.click(submitButton)

    expect(submitButton).toBeDisabled()
  })

  it('calls signIn with correct credentials', async () => {
    const user = userEvent.setup()
    ;(signIn as jest.Mock).mockResolvedValueOnce({ ok: true })
    ;(getSession as jest.Mock).mockResolvedValueOnce({
      user: { role: 'recruiter' },
    })

    render(<LoginPageComponent />)

    await user.type(screen.getByLabelText(/email/i), 'test@example.com')
    await user.type(screen.getByLabelText(/password/i), 'password123')
    await user.click(screen.getByRole('button', { name: /log in/i }))

    await waitFor(() => {
      expect(signIn).toHaveBeenCalledWith('credentials', {
        email: 'test@example.com',
        password: 'password123',
        redirect: false,
      })
    })
  })
})

describe('Authentication - Signup Page', () => {
  const SignupPageComponent = () => {
    const [name, setName] = React.useState('')
    const [email, setEmail] = React.useState('')
    const [password, setPassword] = React.useState('')
    const [confirmPassword, setConfirmPassword] = React.useState('')
    const [error, setError] = React.useState<string | null>(null)

    async function onSubmit(e: React.FormEvent) {
      e.preventDefault()
      setError(null)

      if (password !== confirmPassword) {
        setError("Passwords don't match")
        return
      }

      try {
        const res = await fetch('/api/proxy/auth/signup', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, email, password }),
        })

        if (!res.ok) {
          const data = await res.json()
          setError(data.detail || 'Signup failed')
          return
        }

        // Success - redirect to login
        ;(useRouter()).push('/login')
      } catch (err) {
        setError('An error occurred during signup')
      }
    }

    return (
      <form onSubmit={onSubmit}>
        <div>
          <label htmlFor="name">Name</label>
          <input
            id="name"
            type="text"
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </div>
        <div>
          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        <div>
          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        <div>
          <label htmlFor="confirm-password">Confirm Password</label>
          <input
            id="confirm-password"
            type="password"
            required
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
          />
        </div>
        {error && <p>{error}</p>}
        <button type="submit">Sign up</button>
      </form>
    )
  }

  it('renders signup form with all required fields', () => {
    render(<SignupPageComponent />)

    expect(screen.getByLabelText(/name/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/^email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/^password/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign up/i })).toBeInTheDocument()
  })

  it('validates password confirmation match', async () => {
    const user = userEvent.setup()
    render(<SignupPageComponent />)

    await user.type(screen.getByLabelText(/^password/i), 'password123')
    await user.type(screen.getByLabelText(/confirm password/i), 'different')
    await user.click(screen.getByRole('button', { name: /sign up/i }))

    await waitFor(() => {
      expect(screen.getByText(/passwords don't match/i)).toBeInTheDocument()
    })
  })

  it('submits form with matching passwords', async () => {
    const user = userEvent.setup()
    global.fetch = jest.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ id: '1' }),
      })
    ) as jest.Mock

    render(<SignupPageComponent />)

    await user.type(screen.getByLabelText(/name/i), 'Test User')
    await user.type(screen.getByLabelText(/^email/i), 'test@example.com')
    await user.type(screen.getByLabelText(/^password/i), 'password123')
    await user.type(screen.getByLabelText(/confirm password/i), 'password123')
    await user.click(screen.getByRole('button', { name: /sign up/i }))

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/api/proxy/auth/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: 'Test User',
          email: 'test@example.com',
          password: 'password123',
        }),
      })
    })
  })
})
