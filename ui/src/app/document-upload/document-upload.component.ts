import { Component, EventEmitter, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { DocumentService } from '../services/document.service';
import { forkJoin } from 'rxjs';
import { finalize } from 'rxjs/operators';

@Component({
  selector: 'app-document-upload',
  templateUrl: './document-upload.component.html',
  styleUrls: ['./document-upload.component.scss'],
  standalone: true,
  imports: [CommonModule, MatSnackBarModule]
})
export class DocumentUploadComponent {
  @Output() uploadSuccess = new EventEmitter<void>();
  files: File[] = [];
  isUploading = false;

  constructor(
    private snackBar: MatSnackBar,
    private documentService: DocumentService
  ) {}

  onFileSelected(event: any) {
    this.files.push(...event.target.files);
  }

  onDragOver(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
  }

  onDragLeave(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
  }

  onDrop(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    if (event.dataTransfer?.files) {
      this.files.push(...Array.from(event.dataTransfer.files));
    }
  }

  removeFile(file: File) {
    this.files = this.files.filter(f => f !== file);
  }

  uploadFiles() {
    if (this.files.length === 0) {
      return;
    }

    this.isUploading = true;
    const uploadObservables = this.files.map(file => this.documentService.uploadDocument(file));

    forkJoin(uploadObservables)
      .pipe(
        finalize(() => {
          this.isUploading = false;
          this.files = [];
        })
      )
      .subscribe({
        next: () => {
          this.snackBar.open('Files uploaded successfully!', 'Close', { duration: 3000 });
          this.uploadSuccess.emit();
        },
        error: (error) => {
          console.error('Error uploading files:', error);
          this.snackBar.open('Error uploading files. Please try again.', 'Close', { duration: 3000 });
        }
      });
  }
}
