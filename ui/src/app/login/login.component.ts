import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { AuthService, AuthResponse } from '../services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatSnackBarModule,
    MatProgressSpinnerModule
  ],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss']
})
export class LoginComponent implements OnInit {
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

  ngOnInit(): void {
    this.router.navigate(['/dashboard']);
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
        } else if (response.response?.token) {
          this.router.navigate(['/dashboard']);
        } else {
          this.snackBar.open('Login failed. Please check your credentials.', 'Close', { duration: 5000 });
          this.isLoading = false;
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
      next: (response: AuthResponse) => {
        if (response.response?.token) {
          this.router.navigate(['/dashboard']);
        } else {
          this.snackBar.open('MFA verification failed.', 'Close', { duration: 5000 });
          this.isLoading = false;
        }
      },
      error: (err: any) => {
        this.snackBar.open(err.error?.error || 'MFA verification failed.', 'Close', { duration: 5000 });
        this.isLoading = false;
      }
    });
  }
}
