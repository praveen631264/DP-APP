
import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatListModule } from '@angular/material/list';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { Document } from '../models/document.model';
import { DocumentService } from '../services/document.service';

@Component({
  selector: 'app-document-detail',
  templateUrl: './document-detail.component.html',
  styleUrls: ['./document-detail.component.scss'],
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatListModule,
    MatIconModule,
    MatProgressSpinnerModule
  ]
})
export class DocumentDetailComponent implements OnInit {
  document: Document | null = null;
  isLoading = true;

  constructor(
    private route: ActivatedRoute,
    private documentService: DocumentService
  ) { }

  ngOnInit(): void {
    const docId = this.route.snapshot.paramMap.get('id');
    if (docId) {
      this.documentService.getDocument(docId).subscribe({
        next: (data: Document) => {
          this.document = data;
          this.isLoading = false;
        },
        error: (err: any) => {
          console.error('Error fetching document:', err);
          this.isLoading = false;
        }
      });
    }
  }

  objectKeys(obj: any): string[] {
    if (!obj) {
        return [];
    }
    return Object.keys(obj);
  }
}
