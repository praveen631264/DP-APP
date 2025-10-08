import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { DocumentService, Document } from '../document.service';
import { ChatComponent } from '../chat/chat';
import { DocumentView } from '../document-view/document-view';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.html',
  styleUrls: ['./dashboard.scss'],
  standalone: true,
  imports: [CommonModule, ChatComponent, DocumentView]
})
export class DashboardComponent implements OnInit {
  selectedFile: File | null = null;
  documents: Document[] = [];
  selectedDocument: Document | null = null;
  useMockData = true; // Set initial state to true

  constructor(private documentService: DocumentService, private cdr: ChangeDetectorRef) { }

  ngOnInit(): void {
    // This is a bit of a hack to get the initial state from the service.
    // A better approach would be to use a shared state management service.
    // @ts-ignore
    this.useMockData = this.documentService.useMockData;
    this.loadDocuments();
  }

  loadDocuments(): void {
    this.documentService.getDocuments().subscribe(docs => {
      this.documents = docs;
      if (this.documents.length > 0) {
        this.selectDocument(this.documents[0]);
        this.cdr.detectChanges(); // Manually trigger change detection
      }
    });
  }

  selectDocument(doc: Document): void {
    this.selectedDocument = doc;
  }

  onFileSelected(event: any): void {
    this.selectedFile = event.target.files[0];
  }

  uploadDocument(): void {
    if (this.selectedFile) {
      this.documentService.uploadDocument(this.selectedFile).subscribe(
        (response: any) => {
          console.log('Upload successful', response);
          this.loadDocuments(); // Refresh the list after upload
        },
        (error: any) => {
          console.error('Upload failed', error);
        }
      );
    }
  }

  toggleMockData(): void {
    this.useMockData = !this.useMockData;
    this.documentService.setUseMock(this.useMockData);
  }

  recategorizeDocument(docId: string): void {
    this.documentService.recategorizeDocument(docId, 'new-category-id', 'explanation').subscribe(
      (response: any) => {
        console.log('Recategorize successful', response);
      },
      (error: any) => {
        console.error('Recategorize failed', error);
      }
    );
  }
}
