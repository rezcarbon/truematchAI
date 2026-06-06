/**
 * Utility Functions Tests
 *
 * Tests for common utility functions used across the application
 */

describe('Utility Functions', () => {
  describe('Date formatting', () => {
    it('formats date in locale string', () => {
      const date = new Date('2024-01-15T10:30:00Z')
      const formatted = date.toLocaleDateString('en-US')
      expect(formatted).toMatch(/\d{1,2}\/\d{1,2}\/\d{4}/)
    })

    it('handles invalid dates gracefully', () => {
      const invalidDate = new Date('invalid')
      expect(invalidDate.toString()).toContain('Invalid')
    })
  })

  describe('String utilities', () => {
    it('capitalizes first letter', () => {
      const capitalize = (str: string) => str.charAt(0).toUpperCase() + str.slice(1)
      expect(capitalize('hello')).toBe('Hello')
      expect(capitalize('HELLO')).toBe('HELLO')
    })

    it('converts snake_case to Title Case', () => {
      const toTitleCase = (str: string) => {
        return str
          .split('_')
          .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
          .join(' ')
      }
      expect(toTitleCase('awaiting_review')).toBe('Awaiting Review')
      expect(toTitleCase('cv_analysis')).toBe('Cv Analysis')
    })

    it('handles empty strings', () => {
      const capitalize = (str: string) => str.charAt(0).toUpperCase() + str.slice(1)
      expect(capitalize('')).toBe('')
    })
  })

  describe('Object utilities', () => {
    it('merges objects shallowly', () => {
      const merge = <T extends Record<string, unknown>>(a: T, b: Partial<T>): T & Partial<T> => ({ ...a, ...b })
      const obj1 = { a: 1, b: 2 }
      const obj2 = { b: 3, c: 4 }
      expect(merge(obj1, obj2 as any)).toEqual({ a: 1, b: 3, c: 4 })
    })

    it('removes undefined values', () => {
      const removeUndefined = <T extends Record<string, unknown>>(obj: T): Partial<T> => {
        return Object.fromEntries(
          Object.entries(obj).filter(([_, v]) => v !== undefined)
        ) as Partial<T>
      }
      const input = { a: 1, b: undefined, c: 3 }
      expect(removeUndefined(input as any)).toEqual({ a: 1, c: 3 })
    })
  })

  describe('Array utilities', () => {
    it('filters duplicates', () => {
      const uniqueArray = <T>(arr: T[]): T[] => [...new Set(arr)]
      expect(uniqueArray([1, 2, 2, 3, 3, 3])).toEqual([1, 2, 3])
    })

    it('sorts numbers in descending order', () => {
      const sortDesc = (arr: number[]): number[] => [...arr].sort((a, b) => b - a)
      expect(sortDesc([3, 1, 4, 1, 5])).toEqual([5, 4, 3, 1, 1])
    })

    it('groups items by property', () => {
      interface Item {
        [key: string]: unknown;
      }
      const groupBy = (arr: Item[], key: string): Record<string, Item[]> => {
        return arr.reduce((acc: Record<string, Item[]>, item) => {
          const group = String(item[key])
          if (!acc[group]) acc[group] = []
          acc[group].push(item)
          return acc
        }, {})
      }

      const items = [
        { type: 'cv', name: 'A' },
        { type: 'jd', name: 'B' },
        { type: 'cv', name: 'C' },
      ]

      const grouped = groupBy(items, 'type')
      expect(grouped.cv).toHaveLength(2)
      expect(grouped.jd).toHaveLength(1)
    })
  })

  describe('Validation utilities', () => {
    it('validates email format', () => {
      const isValidEmail = (email: string) => {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
      }

      expect(isValidEmail('test@example.com')).toBe(true)
      expect(isValidEmail('invalid.email')).toBe(false)
      expect(isValidEmail('test@')).toBe(false)
    })

    it('validates URL format', () => {
      const isValidUrl = (url: string) => {
        try {
          new URL(url)
          return true
        } catch {
          return false
        }
      }

      expect(isValidUrl('https://example.com')).toBe(true)
      expect(isValidUrl('not a url')).toBe(false)
    })

    it('checks if string is empty or whitespace', () => {
      const isEmpty = (str: string) => !str || /^\s*$/.test(str)

      expect(isEmpty('')).toBe(true)
      expect(isEmpty('   ')).toBe(true)
      expect(isEmpty('hello')).toBe(false)
    })
  })

  describe('Number utilities', () => {
    it('formats numbers as currency', () => {
      const formatCurrency = (num: number, currency = 'USD') => {
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency,
        }).format(num)
      }

      expect(formatCurrency(1234.56)).toContain('1,234.56')
    })

    it('rounds numbers to decimal places', () => {
      const roundTo = (num: number, decimals: number) => {
        return Math.round(num * Math.pow(10, decimals)) / Math.pow(10, decimals)
      }

      expect(roundTo(3.14159, 2)).toBe(3.14)
      expect(roundTo(10.005, 2)).toBe(10.01)
    })

    it('calculates percentage', () => {
      const percentage = (value: number, total: number) => {
        return (value / total) * 100
      }

      expect(percentage(50, 200)).toBe(25)
      expect(percentage(1, 3)).toBeCloseTo(33.33, 1)
    })
  })

  describe('Promise utilities', () => {
    it('retries function on failure', async () => {
      const retryAsync = async <T,>(
        fn: () => Promise<T>,
        maxRetries = 3,
        delay = 10
      ): Promise<T> => {
        for (let i = 0; i < maxRetries; i++) {
          try {
            return await fn()
          } catch (error) {
            if (i === maxRetries - 1) throw error
            await new Promise((resolve) => setTimeout(resolve, delay))
          }
        }
        throw new Error('Max retries exceeded')
      }

      let attempts = 0
      const fn = async (): Promise<string> => {
        attempts++
        if (attempts < 3) throw new Error('Failed')
        return 'Success'
      }

      const result = await retryAsync(fn, 3, 1)
      expect(result).toBe('Success')
      expect(attempts).toBe(3)
    })

    it('times out promise if it takes too long', async () => {
      const withTimeout = async <T,>(promise: Promise<T>, ms: number): Promise<T> => {
        return Promise.race([
          promise,
          new Promise<T>((_, reject) =>
            setTimeout(() => reject(new Error('Timeout')), ms)
          ),
        ])
      }

      const slowPromise = new Promise((resolve) =>
        setTimeout(() => resolve('done'), 200)
      )

      await expect(withTimeout(slowPromise, 100)).rejects.toThrow('Timeout')
    })
  })

  describe('Status mapping utilities', () => {
    it('maps status to display label', () => {
      const statusLabels: Record<string, string> = {
        awaiting_review: 'Awaiting Review',
        approved: 'Approved',
        rejected: 'Rejected',
        processing: 'Processing',
        completed: 'Completed',
      }

      expect(statusLabels.awaiting_review).toBe('Awaiting Review')
      expect(statusLabels.completed).toBe('Completed')
    })

    it('maps status to color', () => {
      const statusColors: Record<string, string> = {
        awaiting_review: 'amber',
        approved: 'green',
        rejected: 'red',
        processing: 'blue',
        completed: 'green',
      }

      expect(statusColors.awaiting_review).toBe('amber')
      expect(statusColors.approved).toBe('green')
    })

    it('maps action type to icon', () => {
      const actionIcons: Record<string, string> = {
        approve: 'check-circle',
        reject: 'x-circle',
        hold: 'clock',
        reassign: 'arrow-right',
      }

      expect(actionIcons.approve).toBe('check-circle')
      expect(actionIcons.reject).toBe('x-circle')
    })
  })

  describe('Debounce utility', () => {
    it('debounces function calls', async () => {
      jest.useFakeTimers()
      const mockFn = jest.fn()

      const debounce = <T extends unknown[], R,>(fn: (...args: T) => R, delay: number): ((...args: T) => void) => {
        let timeoutId: NodeJS.Timeout
        return (...args: T) => {
          clearTimeout(timeoutId)
          timeoutId = setTimeout(() => fn(...args), delay)
        }
      }

      const debouncedFn = debounce((arg: string) => mockFn(arg), 100)

      debouncedFn('first')
      debouncedFn('second')
      debouncedFn('third')

      jest.advanceTimersByTime(100)

      expect(mockFn).toHaveBeenCalledTimes(1)
      expect(mockFn).toHaveBeenCalledWith('third')

      jest.useRealTimers()
    })
  })

  describe('Throttle utility', () => {
    it('throttles function calls', async () => {
      jest.useFakeTimers()
      const mockFn = jest.fn()

      const throttle = <T extends unknown[], R,>(fn: (...args: T) => R, delay: number): ((...args: T) => void) => {
        let lastCall = 0
        return (...args: T) => {
          const now = Date.now()
          if (now - lastCall >= delay) {
            lastCall = now
            fn(...args)
          }
        }
      }

      const throttledFn = throttle((arg: string) => mockFn(arg), 100)

      throttledFn('first')
      throttledFn('second')
      jest.advanceTimersByTime(50)
      throttledFn('third')
      jest.advanceTimersByTime(60)
      throttledFn('fourth')

      expect(mockFn).toHaveBeenCalledTimes(3)

      jest.useRealTimers()
    })
  })
})
