import { Component, Inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, FormArray, ReactiveFormsModule, Validators } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { CdkDragDrop, DragDropModule, moveItemInArray } from '@angular/cdk/drag-drop';
import { CategoryService, PromptSuggestion } from '../services/category.service';
import { finalize } from 'rxjs/operators';

@Component({
  selector: 'app-category-dialog',
  templateUrl: './category-dialog.component.html',
  styleUrls: ['./category-dialog.component.scss'],
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, DragDropModule]
})
export class CategoryDialogComponent implements OnInit {
  categoryForm: FormGroup;
  isSuggesting = false;

  constructor(
    private fb: FormBuilder,
    private dialogRef: MatDialogRef<CategoryDialogComponent>,
    private categoryService: CategoryService,
    @Inject(MAT_DIALOG_DATA) public data: any
  ) {
    this.categoryForm = this.fb.group({
      name: ['', Validators.required],
      description: [''],
      prompt: ['', Validators.required],
      workflowSteps: this.fb.array([])
    });
  }

  ngOnInit(): void {
    if (this.data?.category) {
      this.categoryForm.patchValue(this.data.category);
      this.data.category.workflowSteps.forEach((step: { name: string }) => {
        this.workflowSteps.push(this.fb.group({ name: [step.name, Validators.required] }));
      });
    }
  }

  get workflowSteps(): FormArray {
    return this.categoryForm.get('workflowSteps') as FormArray;
  }

  addStep(stepName: string): void {
    if (!stepName || this.workflowSteps.value.some((step: {name: string}) => step.name === stepName)) return; // Prevent empty or duplicate steps

    const newStepGroup = this.fb.group({ name: [stepName, Validators.required] });
    this.workflowSteps.push(newStepGroup);
  }

  removeStep(index: number): void {
    this.workflowSteps.removeAt(index);
  }

  drop(event: CdkDragDrop<string[]>): void {
    // Reorder the controls in the FormArray
    moveItemInArray(this.workflowSteps.controls, event.previousIndex, event.currentIndex);
    // Update the form's value and validity to reflect the change
    this.workflowSteps.updateValueAndValidity();
  }

  getPromptSuggestion() {
    this.isSuggesting = true;
    const description = this.categoryForm.get('description')?.value || '';
    this.categoryService.getPromptSuggestion(description).pipe(
      finalize(() => this.isSuggesting = false)
    ).subscribe((suggestion: PromptSuggestion) => {
      this.categoryForm.get('prompt')?.setValue(suggestion.prompt);
    });
  }

  onSave(): void {
    if (this.categoryForm.valid) {
      this.dialogRef.close(this.categoryForm.value);
    }
  }

  onCancel(): void {
    this.dialogRef.close();
  }
}
