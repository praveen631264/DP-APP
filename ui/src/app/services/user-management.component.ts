import { Component, OnInit } from '@angular/core';
import { Observable, BehaviorSubject } from 'rxjs';
import { switchMap } from 'rxjs/operators';
import { AdminService, User, Policy } from '../services/admin.service';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatDialog } from '@angular/material/dialog';
import { ConfirmationDialogComponent } from '../dialogs/confirmation-dialog/confirmation-dialog.component';
import { MatSnackBar } from '@angular/material/snack-bar';

@Component({
  selector: 'app-user-management',
  templateUrl: './user-management.component.html',
  styleUrls: ['./user-management.component.scss']
})
export class UserManagementComponent implements OnInit {
  
  private refreshUsers$ = new BehaviorSubject<void>(undefined);
  private refreshPolicies$ = new BehaviorSubject<void>(undefined);

  users$: Observable<User[]>;
  policies$: Observable<Policy[]>;
  allRoles$: Observable<string[]>;

  displayedColumns: string[] = ['email', 'roles', 'status', 'mfa_enabled', 'actions'];
  policyForm: FormGroup;
  
  constructor(
    private adminService: AdminService,
    private snackBar: MatSnackBar,
    private fb: FormBuilder,
    private dialog: MatDialog
  ) {
    this.users$ = this.refreshUsers$.pipe(
      switchMap(() => this.adminService.getUsers())
    );
    this.policies$ = this.refreshPolicies$.pipe(
      switchMap(() => this.adminService.getPolicies())
    );
    this.allRoles$ = this.adminService.getRoles();
    this.policyForm = this.fb.group({
      resource: ['', Validators.required],
      policy: ['{}', Validators.required], // Storing policy as a JSON string for simplicity
      description: ['']
    });
  }

  ngOnInit(): void {
  }

  approveUser(user: User): void {
    this.adminService.updateUser(user.id, { approved: true }).subscribe({
      next: () => {
        this.snackBar.open(`User ${user.email} approved successfully.`, 'Close', { duration: 3000 });
        this.refreshUsers$.next(); // Trigger a refresh of the user list
      },
      error: (err: any) => {
        this.snackBar.open(`Failed to approve user: ${err.error?.error || 'Unknown error'}`, 'Close', { duration: 5000 });
      }
    });
  }

  onRolesChange(newRoles: string[], user: User): void {
    this.adminService.updateUser(user.id, { roles: newRoles }).subscribe({
      next: () => {
        this.snackBar.open(`Roles updated for ${user.email}.`, 'Close', { duration: 3000 });
        // Trigger a refresh to ensure the UI reflects the canonical state from the server.
        this.refreshUsers$.next();
      },
      error: (err: any) => {
        this.snackBar.open(`Failed to update roles: ${err.error?.error || 'Unknown error'}`, 'Close', { duration: 5000 });
      }
    });
  }

  resetMfa(user: User): void {
    const dialogRef = this.dialog.open(ConfirmationDialogComponent, {
      data: {
        title: 'Confirm MFA Reset',
        message: `Are you sure you want to reset Two-Factor Authentication for ${user.email}? They will need to set it up again.`,
        confirmButtonText: 'Reset MFA',
        confirmButtonColor: 'warn'
      }
    });

    dialogRef.afterClosed().subscribe((confirmed: any) => {
      if (confirmed) {
        this.adminService.resetMfa(user.id).subscribe({
          next: () => {
            this.snackBar.open(`MFA has been reset for ${user.email}.`, 'Close', { duration: 3000 });
            this.refreshUsers$.next();
          },
          error: (err: any) => this.snackBar.open(`Failed to reset MFA: ${err.error?.error || 'Unknown error'}`, 'Close', { duration: 5000 })
        });
      }
    });
  }

  createPolicy(): void {
    if (this.policyForm.invalid) {
      return;
    }
    try {
      const policyValue = JSON.parse(this.policyForm.value.policy);
      const newPolicy: Policy = {
        resource: this.policyForm.value.resource,
        policy: policyValue,
        description: this.policyForm.value.description
      };

      this.adminService.createPolicy(newPolicy).subscribe({
        next: () => {
          this.snackBar.open('Policy created successfully.', 'Close', { duration: 3000 });
          this.refreshPolicies$.next();
          this.policyForm.reset({ policy: '{}' });
        },
        error: (err: any) => {
          this.snackBar.open(`Failed to create policy: ${err.error?.error || 'Unknown error'}`, 'Close', { duration: 5000 });
        }
      });
    } catch (e) {
      this.snackBar.open('Invalid JSON in policy field.', 'Close', { duration: 3000 });
    }
  }

  deletePolicy(policy: Policy): void {
    const dialogRef = this.dialog.open(ConfirmationDialogComponent, {
      data: {
        title: 'Confirm Policy Deletion',
        message: `Are you sure you want to delete the policy for resource "${policy.resource}"?`,
        confirmButtonText: 'Delete',
        confirmButtonColor: 'warn'
      }
    });

    dialogRef.afterClosed().subscribe((confirmed: any) => {
      if (confirmed) {
        this.adminService.deletePolicy(policy.resource).subscribe({
          next: () => {
            this.snackBar.open('Policy deleted successfully.', 'Close', { duration: 3000 });
            this.refreshPolicies$.next();
          },
          error: (err: any) => this.snackBar.open(`Failed to delete policy: ${err.error?.error || 'Unknown error'}`, 'Close', { duration: 5000 })
        });
      }
    });
  }
}