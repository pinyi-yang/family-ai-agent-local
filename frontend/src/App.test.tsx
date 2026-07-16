import { test, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import App from './App';

test('renders dashboard heading', () => {
  render(<App />);
  const headingElement = screen.getByRole('heading', { level: 1, name: /Family AI Agent/i });
  expect(headingElement).toBeInTheDocument();
});
