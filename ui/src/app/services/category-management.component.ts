import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatDialog } from '@angular/material/dialog';
import { PlaybookEditorComponent } from '../playbook-editor/playbook-editor.component';
import { ConfirmationDialogComponent } from '../confirmation-dialog/confirmation-dialog.component';
import { CategoryService, CategoryPlaybook } from '../../services/category.service';
import { Observable, BehaviorSubject } from 'rxjs';
import { switchMap } from 'rxjs/operators';

@Component({
  selector: 'app-category-management',
  templateUrl: './category-management.component.html',
  styleUrls: ['./category-management.component.scss']
})
export class CategoryManagementComponent implements OnInit {

  private refreshCategories$ = new BehaviorSubject<void>(undefined);
  categories$: Observable<CategoryPlaybook[]>;
  categoryForm: FormGroup;
  isCreating = false;

  constructor(
    private categoryService: CategoryService,
    private fb: FormBuilder,
    private snackBar: MatSnackBar,
    private dialog: MatDialog
  ) {
    this.categories$ = this.refreshCategories$.pipe(
      switchMap(() => this.categoryService.getCategories())
    );
    this.categoryForm = this.fb.group({
      name: ['', [Validators.required, Validators.pattern(/^[a-zA-Z0-9\s-_]+$/)]],
      description: ['']
    });
  }

  ngOnInit(): void {
  }

  onSubmit(): void {
    if (this.categoryForm.invalid) {
      return;
    }

    this.isCreating = true;
    const newCategory: CategoryPlaybook = {
      name: this.categoryForm.value.name,
      description: this.categoryForm.value.description
    };

    this.categoryService.createCategory(newCategory).subscribe({
      next: () => {
        this.snackBar.open(`Category '${newCategory.name}' created successfully!`, 'Close', { duration: 3000 });
        this.refreshCategories$.next(); // Trigger a refresh of the list
        this.categoryForm.reset();
        this.isCreating = false;
      },
      error: (err: any) => {
        const errorMessage = err.error?.error || 'Failed to create category.';
        this.snackBar.open(`Error: ${errorMessage}`, 'Close', { duration: 5000 });
        this.isCreating = false;
      }
    });
  }

  openPlaybookEditor(playbook: CategoryPlaybook): void {
    const dialogRef = this.dialog.open(PlaybookEditorComponent, {
      width: '800px',
      data: { playbook }
    });

    dialogRef.afterClosed().subscribe((result: any) => {
      if (result) { // If the dialog returned true (i.e., was saved)
        this.refreshCategories$.next(); // Refresh the list
      }
    });
  }

  deleteCategory(playbook: CategoryPlaybook): void {
    const dialogRef = this.dialog.open(ConfirmationDialogComponent, {
      data: {
        title: 'Confirm Deletion',
        message: `Are you sure you want to delete the category playbook "${playbook.name}"? This action cannot be undone.`,
        confirmButtonText: 'Delete',
        confirmButtonColor: 'warn'
      }
    });

    dialogRef.afterClosed().subscribe((confirmed: any) => {
      if (confirmed) {
        this.categoryService.deleteCategory(playbook.name).subscribe({
          next: () => {
            this.snackBar.open(`Category '${playbook.name}' deleted successfully.`, 'Close', { duration: 3000 });
            this.refreshCategories$.next(); // Refresh the list
          },
          error: (err: any) => {
            const errorMessage = err.error?.error || 'Failed to delete category.';
            this.snackBar.open(`Error: ${errorMessage}`, 'Close', { duration: 5000 });
          }
        });
      }
    });
  }
}