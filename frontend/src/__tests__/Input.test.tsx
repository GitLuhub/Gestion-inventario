import React from 'react'
import { render, screen } from '@testing-library/react'
import { Input, Select } from '@/components/ui/Input'

describe('Input', () => {
  it('renders input element', () => {
    render(<Input />)
    expect(screen.getByRole('textbox')).toBeInTheDocument()
  })

  it('displays label when provided', () => {
    render(<Input label="Email" />)
    expect(screen.getByLabelText('Email')).toBeInTheDocument()
  })

  it('displays error message when provided', () => {
    render(<Input error="This field is required" />)
    expect(screen.getByText('This field is required')).toBeInTheDocument()
  })

  it('displays helper text when provided', () => {
    render(<Input helperText="Enter your email" />)
    expect(screen.getByText('Enter your email')).toBeInTheDocument()
  })

  it('applies error styling when error prop is provided', () => {
    render(<Input error="Error" />)
    const input = screen.getByRole('textbox')
    expect(input).toHaveClass('border-danger-500')
  })

  it('does not render helper text when error is also provided', () => {
    render(<Input error="Bad input" helperText="Helper" />)
    expect(screen.queryByText('Helper')).not.toBeInTheDocument()
  })

  it('uses provided id for label association', () => {
    render(<Input id="my-input" label="Name" />)
    const input = screen.getByLabelText('Name')
    expect(input).toHaveAttribute('id', 'my-input')
  })
})

describe('Select', () => {
  const options = [
    { value: '1', label: 'Option A' },
    { value: '2', label: 'Option B' },
  ]

  it('renders a combobox with the provided options', () => {
    render(<Select options={options} />)
    expect(screen.getByRole('combobox')).toBeInTheDocument()
    expect(screen.getByText('Option A')).toBeInTheDocument()
    expect(screen.getByText('Option B')).toBeInTheDocument()
  })

  it('displays label when provided', () => {
    render(<Select label="Category" options={options} />)
    expect(screen.getByText('Category')).toBeInTheDocument()
  })

  it('displays error message when provided', () => {
    render(<Select error="Required" options={options} />)
    expect(screen.getByText('Required')).toBeInTheDocument()
  })

  it('applies error styling when error prop is provided', () => {
    render(<Select error="Bad" options={[]} />)
    const select = screen.getByRole('combobox')
    expect(select).toHaveClass('border-danger-500')
  })

  it('renders without options', () => {
    render(<Select options={[]} />)
    expect(screen.getByRole('combobox')).toBeInTheDocument()
  })
})
