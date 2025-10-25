import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ICellRendererAngularComp } from 'ag-grid-angular';
import { ICellRendererParams } from 'ag-grid-community';
import { DocumentService } from '../services/document.service';
import { Router } from '@angular/router';
import { saveAs } from 'file-saver';

@Component({
  selector: 'app-actions-cell-renderer',
  template: `
    <div class="actions-container">
      <button (click)="onView()">View</button>
      <button (click)="onDownload()">Download</button>
      <button (click)="onDelete()">Delete</button>
    </div>
  `,
  styles: [`
    .actions-container {
      display: flex;
      gap: 5px;
    }
    button {
      padding: 2px 5px;
      font-size: 12px;
    }
  `],
  standalone: true,
  imports: [CommonModule],
})
export class ActionsCellRendererComponent implements ICellRendererAngularComp {
  private params!: ICellRendererParams;

  constructor(
    private router: Router,
    private documentService: DocumentService
  ) {}

  agInit(params: ICellRendererParams): void {
    this.params = params;
  }

  refresh(params: ICellRendererParams): boolean {
    this.params = params;
    return true;
  }

  onView(): void {
    // Assuming a route like '/documents/:id' exists
    this.router.navigate(['/documents', this.params.data._id]);
  }

  onDownload(): void {
    this.documentService.downloadDocument(this.params.data._id).subscribe((blob: Blob) => {
      saveAs(blob, this.params.data.filename);
    });
  }

  onDelete(): void {
    if (confirm('Are you sure you want to delete this document?')) {
      this.documentService.deleteDocument(this.params.data._id).subscribe(() => {
        // Optionally, refresh the grid here
        this.params.api.applyTransaction({ remove: [this.params.data] });
      });
    }
  }
}
