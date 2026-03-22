import { cn } from '@/lib/utils'

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
})
