import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

@Component({
  selector: 'app-document-upload',
  templateUrl: './document-upload.component.html',
  styleUrls: ['./document-upload.component.scss'],
  standalone: true,
  imports: [CommonModule, MatSnackBarModule]
})
export class DocumentUploadComponent {
  files: File[] = [];

  constructor(private snackBar: MatSnackBar) {}

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
    // Implement the upload logic here
    console.log('Uploading files:', this.files);
    this.snackBar.open('Files uploaded successfully!', 'Close', { duration: 3000 });
    this.files = [];
  }
}