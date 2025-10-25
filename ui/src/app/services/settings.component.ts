import { Component, OnInit } from '@angular/core';
import { ThemeService, Theme } from '../services/theme.service';
import { ProfileService, UserProfile } from '../services/profile.service';
import { MatSnackBar } from '@angular/material/snack-bar';
import { FormBuilder, FormGroup, Validators, ValidatorFn, AbstractControl, ValidationErrors } from '@angular/forms';
import * as QRCode from 'qrcode';
import { Observable, BehaviorSubject } from 'rxjs';
import { AuthService } from '../services/auth.service';

@Component({
  selector: 'app-settings',
  templateUrl: './settings.component.html',
  styleUrls: ['./settings.component.scss']
})
export class SettingsComponent implements OnInit {

  availableThemes: Theme[];
  activeTheme$: Observable<string>;
  currentUserEmail$: Observable<string | null>;
  passwordForm: FormGroup;
  mfaSetupForm: FormGroup;
  mfaDisableForm: FormGroup;
  mfaQrCode: string | null = null;
  isSettingUpMfa = false;
  mfaEnabled$ = new BehaviorSubject<boolean>(false);

  constructor(
    public themeService: ThemeService,
    private profileService: ProfileService,
    private authService: AuthService,
    private snackBar: MatSnackBar,
    private fb: FormBuilder
  ) {
    this.availableThemes = this.themeService.availableThemes;
    this.activeTheme$ = this.themeService.getActiveTheme();
    this.currentUserEmail$ = this.authService.currentUserEmail$;

    this.passwordForm = this.fb.group({
      currentPassword: ['', Validators.required],
      newPassword: ['', [Validators.required, Validators.minLength(8)]],
      confirmPassword: ['', Validators.required]
    }, {
      validators: this.passwordMatchValidator
    });

    this.mfaSetupForm = this.fb.group({
      totp_code: ['', [Validators.required, Validators.minLength(6), Validators.maxLength(6)]]
    });

    this.mfaDisableForm = this.fb.group({
      totp_code: ['', [Validators.required, Validators.minLength(6), Validators.maxLength(6)]]
    });
  }

  ngOnInit(): void {
    this.profileService.getProfile().subscribe((profile: UserProfile) => {
      this.mfaEnabled$.next(profile.mfa_enabled);
    });
  }

  onThemeChange(themeName: string): void {
    this.themeService.setTheme(themeName);
    this.profileService.updatePreferences({ theme: themeName }).subscribe({
      next: () => this.snackBar.open('Theme preference saved!', 'Close', { duration: 2000 }),
      error: () => this.snackBar.open('Failed to save theme preference.', 'Close', { duration: 3000 })
    });
  }

  changePassword(): void {
    if (this.passwordForm.invalid) {
      return;
    }
    const payload = {
      currentPassword: this.passwordForm.value.currentPassword,
      newPassword: this.passwordForm.value.newPassword
    };
    this.profileService.changePassword(payload).subscribe({
      next: () => {
        this.snackBar.open('Password changed successfully!', 'Close', { duration: 3000 });
        this.passwordForm.reset();
      },
      error: (err: any) => {
        this.snackBar.open(`Error: ${err.error?.error || 'Failed to change password.'}`, 'Close', { duration: 5000 });
      }
    });
  }

  private passwordMatchValidator: ValidatorFn = (control: AbstractControl): ValidationErrors | null => {
    const newPassword = control.get('newPassword');
    const confirmPassword = control.get('confirmPassword');
    return newPassword && confirmPassword && newPassword.value !== confirmPassword.value
      ? { passwordMismatch: true }
      : null;
  };

  initiateMfaSetup(): void {
    this.isSettingUpMfa = true;
    this.profileService.setupMfa().subscribe({
      next: (response: { provisioning_uri: string }) => {
        QRCode.toDataURL(response.provisioning_uri, (err: any, url: string) => {
          if (err) {
            this.snackBar.open('Error generating QR code.', 'Close', { duration: 3000 });
            this.isSettingUpMfa = false;
          } else {
            this.mfaQrCode = url;
          }
        });
      },
      error: () => {
        this.snackBar.open('Failed to start MFA setup.', 'Close', { duration: 3000 });
        this.isSettingUpMfa = false;
      }
    });
  }

  verifyMfa(): void {
    if (this.mfaSetupForm.invalid) return;

    const code = this.mfaSetupForm.value.totp_code;
    this.profileService.verifyMfa(code).subscribe({
      next: () => {
        this.snackBar.open('Two-Factor Authentication enabled successfully!', 'Close', { duration: 3000 });
        this.mfaQrCode = null;
        this.isSettingUpMfa = false;
        this.mfaEnabled$.next(true);
      },
      error: (err: any) => this.snackBar.open(`Error: ${err.error?.error || 'Verification failed.'}`, 'Close', { duration: 5000 })
    });
  }

  disableMfa(): void {
    if (this.mfaDisableForm.invalid) return;

    const code = this.mfaDisableForm.value.totp_code;
    this.profileService.disableMfa(code).subscribe({
      next: () => {
        this.snackBar.open('Two-Factor Authentication has been disabled.', 'Close', { duration: 3000 });
        this.mfaEnabled$.next(false);
        this.mfaDisableForm.reset();
      },
      error: (err: any) => this.snackBar.open(`Error: ${err.error?.error || 'Could not disable MFA.'}`, 'Close', { duration: 5000 })
    });
  }
}