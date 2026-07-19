import { test, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import App from './App';

test('renders dashboard heading', () => {
  render(<App />);
  const headingElement = screen.getByRole('heading', { level: 1, name: /Family AI Agent/i });
  expect(headingElement).toBeInTheDocument();
});

test('can navigate to Integration Tests tab', () => {
  render(<App />);
  
  // Find the Integration Tests navigation link and click it
  const testsNavLink = screen.getByRole('button', { name: /Integration Tests/i });
  expect(testsNavLink).toBeInTheDocument();
  
  fireEvent.click(testsNavLink);
  
  // After clicking, the sub-tabs for Slack Bot Test and Google Workspace Test should be visible
  const slackSubTab = screen.getByRole('button', { name: /Slack Bot Test/i });
  const googleSubTab = screen.getByRole('button', { name: /Google Workspace Test/i });
  
  expect(slackSubTab).toBeInTheDocument();
  expect(googleSubTab).toBeInTheDocument();
});
