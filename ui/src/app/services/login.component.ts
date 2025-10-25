import { Component } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { MatSnackBar } from '@angular/material/snack-bar';
import { AuthService, AuthResponse } from '../services/auth.service';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss']
})
export class LoginComponent {
  loginForm: FormGroup;
  isLoading = false;
  mfaRequired = false;
  mfaForm: FormGroup;

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
    private router: Router,
    private snackBar: MatSnackBar
  ) {
    this.loginForm = this.fb.group({
      email: ['admin@example.com', [Validators.required, Validators.email]],
      password: ['password', Validators.required]
    });

    this.mfaForm = this.fb.group({
      totp_code: ['', [Validators.required, Validators.minLength(6), Validators.maxLength(6)]]
    });
  }

  onSubmit(): void {
    if (this.loginForm.invalid) {
      return;
    }
    this.isLoading = true;
    this.authService.login(this.loginForm.value).subscribe({
      next: (response: AuthResponse) => {
        if (response.mfa_required) {
          this.mfaRequired = true;
          this.isLoading = false;
        } else {
          this.router.navigate(['/dashboard']);
        }
      },
      error: (err: any) => {
        this.snackBar.open(err.error?.error || 'Login failed. Please check your credentials.', 'Close', { duration: 5000 });
        this.isLoading = false;
      }
    });
  }

  onMfaSubmit(): void {
    if (this.mfaForm.invalid) {
      return;
    }
    this.isLoading = true;
    const email = this.loginForm.value.email;
    const totp_code = this.mfaForm.value.totp_code;

    this.authService.loginWithMfa(email, totp_code).subscribe({
      next: () => this.router.navigate(['/dashboard']),
      error: (err: any) => {
        this.snackBar.open(err.error?.error || 'MFA verification failed.', 'Close', { duration: 5000 });
        this.isLoading = false;
      }
    });
  }
}