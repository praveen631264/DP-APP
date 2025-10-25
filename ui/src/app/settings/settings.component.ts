
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Observable, of } from 'rxjs';

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatButtonModule,
    MatSnackBarModule,
    ReactiveFormsModule,
    MatProgressSpinnerModule
  ],
  templateUrl: './settings.component.html',
  styleUrls: ['./settings.component.scss']
})
export class SettingsComponent implements OnInit {
  currentUserEmail$: Observable<string | undefined> = of('admin@example.com');
  activeTheme$: Observable<string> = of('deep-purple-amber');
  availableThemes = [{name: 'deep-purple-amber', displayName: 'Deep Purple & Amber'}, {name: 'dark-theme', displayName: 'Dark Theme'}];
  passwordForm: FormGroup;
  mfaEnabled$: Observable<boolean> = of(false);
  isSettingUpMfa = false;
  mfaQrCode: string | null = null;
  mfaSetupForm: FormGroup;
  mfaDisableForm: FormGroup;

  constructor(private fb: FormBuilder, private snackBar: MatSnackBar) {
    this.passwordForm = this.fb.group({
      currentPassword: ['', Validators.required],
      newPassword: ['', [Validators.required, Validators.minLength(8)]],
      confirmPassword: ['', Validators.required]
    }, { validator: this.passwordMatchValidator });

    this.mfaSetupForm = this.fb.group({
      totp_code: ['', [Validators.required, Validators.minLength(6), Validators.maxLength(6)]]
    });

    this.mfaDisableForm = this.fb.group({
      totp_code: ['', [Validators.required, Validators.minLength(6), Validators.maxLength(6)]]
    });
  }

  ngOnInit(): void {
  }

  passwordMatchValidator(form: FormGroup) {
    const newPassword = form.get('newPassword')?.value;
    const confirmPassword = form.get('confirmPassword')?.value;
    return newPassword === confirmPassword ? null : { passwordMismatch: true };
  }

  onThemeChange(theme: string) {
    this.snackBar.open(`Theme changed to ${theme}`, 'Close', { duration: 3000 });
  }

  changePassword() {
    if (this.passwordForm.valid) {
      this.snackBar.open('Password changed successfully', 'Close', { duration: 3000 });
    }
  }

  initiateMfaSetup() {
    this.isSettingUpMfa = true;
    // In a real app, you would call a service to get the QR code
    this.mfaQrCode = 'https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=otpauth://totp/IntelliDocs:admin@example.com?secret=JBSWY3DPEHPK3PXP&issuer=IntelliDocs';
  }

  verifyMfa() {
    if (this.mfaSetupForm.valid) {
      this.snackBar.open('MFA enabled successfully', 'Close', { duration: 3000 });
      this.isSettingUpMfa = false;
      this.mfaEnabled$ = of(true);
    }
  }

  disableMfa() {
    if (this.mfaDisableForm.valid) {
      this.snackBar.open('MFA disabled successfully', 'Close', { duration: 3000 });
      this.mfaEnabled$ = of(false);
    }
  }
}
