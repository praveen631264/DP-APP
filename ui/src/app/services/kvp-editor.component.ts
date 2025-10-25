import { Component, Input, OnChanges, SimpleChanges } from '@angular/core';
import { FormBuilder, FormGroup, FormControl } from '@angular/forms';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Document, DocumentService } from '../../services/document.service';

@Component({
  selector: 'app-kvp-editor',
  templateUrl: './kvp-editor.component.html',
  styleUrls: ['./kvp-editor.component.scss']
})
export class KvpEditorComponent implements OnChanges {
  @Input() document: Document | null = null;

  isEditing = false;
  kvpForm: FormGroup = this.fb.group({});
  originalFormValue: any = {};

  constructor(
    private fb: FormBuilder,
    private documentService: DocumentService,
    private snackBar: MatSnackBar
  ) {}

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['document'] && this.document) {
      this.buildForm();
    }
  }

  get kvpAsArray(): { key: string, value: any }[] {
    if (!this.document || !this.document.kvp) {
      return [];
    }
    return Object.entries(this.document.kvp)
      .map(([key, value]) => ({ key, value }))
      .sort((a, b) => a.key.localeCompare(b.key));
  }

  private buildForm(): void {
    if (!this.document || !this.document.kvp) {
      this.kvpForm = this.fb.group({});
      return;
    }
    const group: { [key: string]: FormControl } = {};
    for (const key in this.document.kvp) {
      if (Object.prototype.hasOwnProperty.call(this.document.kvp, key)) {
        group[key] = new FormControl(this.document.kvp[key]);
      }
    }
    this.kvpForm = this.fb.group(group);
    this.originalFormValue = this.kvpForm.getRawValue();
  }

  toggleEditMode(): void {
    this.isEditing = !this.isEditing;
    if (!this.isEditing) {
      this.kvpForm.reset(this.originalFormValue); // Revert changes on cancel
    }
  }

  onSave(): void {
    if (this.kvpForm.invalid || !this.document?._id || this.document._version === undefined) {
      return;
    }

    this.documentService.updateKvp(this.document._id, this.kvpForm.value, this.document._version).subscribe({
      next: (response) => {
        this.snackBar.open('Extracted data updated successfully!', 'Close', { duration: 3000 });
        this.isEditing = false;
        // IMPORTANT: The parent component should update the document object
        // with response.document to get the new _version number.
        // For now, we optimistically update the local state.
        this.document = response.document;
        this.buildForm();
      },
      error: (err) => {
        const errorMessage = err.error?.error || 'Failed to update data.';
        this.snackBar.open(`Error: ${errorMessage}`, 'Close', { duration: 5000 });
      }
    });
  }
}