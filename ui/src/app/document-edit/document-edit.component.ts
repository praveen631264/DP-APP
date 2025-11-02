
import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { FormBuilder, FormGroup, ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { Document } from '../models/document.model';
import { DocumentService } from '../services/document.service';

@Component({
  selector: 'app-document-edit',
  templateUrl: './document-edit.component.html',
  styleUrls: ['./document-edit.component.scss'],
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatProgressSpinnerModule
  ]
})
export class DocumentEditComponent implements OnInit {
  document: Document | null = null;
  editForm: FormGroup;
  isLoading = true;
  isSaving = false;

  constructor(
    private route: ActivatedRoute,
    public router: Router, // Made public
    private fb: FormBuilder,
    private documentService: DocumentService
  ) {
    this.editForm = this.fb.group({});
  }

  ngOnInit(): void {
    const docId = this.route.snapshot.paramMap.get('id');
    if (docId) {
      this.documentService.getDocument(docId).subscribe({
        next: (data: Document) => {
          this.document = data;
          this.buildForm();
          this.isLoading = false;
        },
        error: (err: any) => {
          console.error('Error fetching document:', err);
          this.isLoading = false;
        }
      });
    }
  }

  buildForm(): void {
    if (this.document && this.document.kvps) {
        const formControls: { [key: string]: any } = {};
        for (const key of Object.keys(this.document.kvps)) {
            formControls[key] = [this.document.kvps[key]];
        }
        this.editForm = this.fb.group(formControls);
    }
  }

  objectKeys(obj: any): string[] {
    if (!obj) {
        return [];
    }
    return Object.keys(obj);
  }

  onSubmit(): void {
    if (this.editForm.valid && this.document) {
      this.isSaving = true;
      this.documentService.updateDocumentKvps(this.document.id, this.editForm.value, this.document._version)
        .subscribe({
          next: () => {
            this.isSaving = false;
            this.router.navigate(['/documents', this.document?.id]);
          },
          error: (err: any) => {
            console.error('Error updating document:', err);
            this.isSaving = false;
          }
        });
    }
  }
}
