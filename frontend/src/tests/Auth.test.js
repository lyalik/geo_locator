import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter as Router } from 'react-router-dom';
import Login from '../components/Login';
import Register from '../components/Register';

test('renders login form and handles submission', () => {
  render(
    <Router>
      <Login />
    </Router>
  );
  const emailInput = screen.getByLabelText(/email/i);
  const passwordInput = screen.getByLabelText(/password/i);
  const loginButton = screen.getByText(/login/i);

  fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
  fireEvent.change(passwordInput, { target: { value: 'testpassword' } });
  fireEvent.click(loginButton);

  // Add assertions to check the expected behavior after form submission
});

test('renders register form and handles submission', () => {
  render(
    <Router>
      <Register />
    </Router>
  );
  const usernameInput = screen.getByLabelText(/username/i);
  const emailInput = screen.getByLabelText(/email/i);
  const passwordInput = screen.getByLabelText(/password/i);
  const registerButton = screen.getByText(/register/i);

  fireEvent.change(usernameInput, { target: { value: 'testuser' } });
  fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
  fireEvent.change(passwordInput, { target: { value: 'testpassword' } });
  fireEvent.click(registerButton);

  // Add assertions to check the expected behavior after form submission
});
