import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Document, DocumentService } from '../../services/document.service';
import { Observable, of } from 'rxjs';
import { catchError } from 'rxjs/operators';

@Component({
  selector: 'app-document-details',
  templateUrl: './document-details.component.html',
  styleUrls: ['./document-details.component.scss']
})
export class DocumentDetailsComponent implements OnInit {
  document$: Observable<Document | null> = of(null);
  isLoading = true;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private documentService: DocumentService,
    private snackBar: MatSnackBar
  ) {}

  ngOnInit(): void {
    const docId = this.route.snapshot.paramMap.get('id');
    if (docId) {
      this.document$ = this.documentService.getDocumentById(docId).pipe(
        catchError(err => {
          this.snackBar.open(`Error loading document: ${err.error?.error || 'Not Found'}`, 'Close', { duration: 5000 });
          this.router.navigate(['/documents']); // Redirect on error
          return of(null);
        })
      );
    }
  }
}