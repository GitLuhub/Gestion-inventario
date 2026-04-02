import { cn, formatCurrency, formatNumber, formatDate, formatDateTime } from '@/lib/utils'

describe('utils', () => {
  describe('cn', () => {
    it('merges class names', () => {
      const result = cn('foo', 'bar')
      expect(result).toBe('foo bar')
    })

    it('handles conditional classes', () => {
      const isActive = true
      const result = cn('base', isActive && 'active')
      expect(result).toBe('base active')
    })

    it('filters out falsy values', () => {
      const result = cn('foo', false, null, undefined, '', 'bar')
      expect(result).toBe('foo bar')
    })

    it('handles nested arrays', () => {
      const result = cn('foo', ['bar', 'baz'])
      expect(result).toBe('foo bar baz')
    })
  })

  describe('formatCurrency', () => {
    it('returns a string', () => {
      expect(typeof formatCurrency(1000)).toBe('string')
    })

    it('formats zero', () => {
      const result = formatCurrency(0)
      expect(typeof result).toBe('string')
      expect(result.length).toBeGreaterThan(0)
    })

    it('contains the digits of the value', () => {
      const result = formatCurrency(1500)
      expect(result).toMatch(/1[.,\s]?500/)
    })
  })

  describe('formatNumber', () => {
    it('returns a string', () => {
      expect(typeof formatNumber(42)).toBe('string')
    })

    it('formats zero as "0"', () => {
      expect(formatNumber(0)).toBe('0')
    })

    it('contains the digits of the value', () => {
      const result = formatNumber(12345)
      expect(result).toMatch(/12/)
      expect(result).toMatch(/345/)
    })
  })

  describe('formatDate', () => {
    it('accepts a date string and returns a string', () => {
      const result = formatDate('2025-01-15')
      expect(typeof result).toBe('string')
      expect(result.length).toBeGreaterThan(0)
    })

    it('accepts a Date object', () => {
      const result = formatDate(new Date('2025-06-01T12:00:00Z'))
      expect(typeof result).toBe('string')
    })

    it('includes the year in the result', () => {
      const result = formatDate('2025-03-20')
      expect(result).toContain('2025')
    })
  })

  describe('formatDateTime', () => {
    it('accepts a date-time string and returns a string', () => {
      const result = formatDateTime('2025-01-15T10:30:00')
      expect(typeof result).toBe('string')
      expect(result.length).toBeGreaterThan(0)
    })

    it('accepts a Date object', () => {
      const result = formatDateTime(new Date('2025-06-01T14:00:00Z'))
      expect(typeof result).toBe('string')
    })

    it('includes the year in the result', () => {
      const result = formatDateTime('2025-03-20T09:00:00')
      expect(result).toContain('2025')
    })
  })
})
