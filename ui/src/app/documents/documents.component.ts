import { AfterViewInit, Component, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatTableDataSource } from '@angular/material/table';
import { MatPaginator, MatPaginatorModule } from '@angular/material/paginator';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { Router } from '@angular/router';
import { BehaviorSubject, Observable, Subject, switchMap, takeUntil, tap } from 'rxjs';

import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTooltipModule } from '@angular/material/tooltip';

import { DocumentService } from '../services/document.service';
import { CategoryService } from '../services/category.service';
import { NotificationService } from '../services/notification.service';

import { DocumentUploadComponent } from '../dialogs/document-upload/document-upload.component';
import {
  ConfirmationDialogComponent,
  ConfirmationDialogData
} from '../dialogs/confirmation-dialog/confirmation-dialog.component';

import { Document } from '../models/document.model';
import { Category } from '../models/category.model';

@Component({
  selector: 'app-documents',
  templateUrl: './documents.component.html',
  styleUrl: './documents.component.scss',
  standalone: true,
  imports: [
    CommonModule,
    MatTableModule,
    MatPaginatorModule,
    MatButtonModule,
    MatIconModule,
    MatFormFieldModule,
    MatSelectModule,
    MatProgressSpinnerModule,
    MatTooltipModule,
    MatDialogModule,
  ]
})
export class DocumentsComponent implements OnInit, AfterViewInit, OnDestroy {
  displayedColumns: string[] = ['filename', 'category', 'status', 'created_at', 'actions'];
  dataSource = new MatTableDataSource<Document>();
  categories$!: Observable<Category[]>;

  private isLoadingSubject = new BehaviorSubject<boolean>(true);
  isLoading$ = this.isLoadingSubject.asObservable();

  private destroy$ = new Subject<void>();
  private refreshDocuments$ = new BehaviorSubject<void>(undefined);

  @ViewChild(MatPaginator) paginator!: MatPaginator;

  constructor(
    private documentService: DocumentService,
    private categoryService: CategoryService,
    private notificationService: NotificationService,
    private dialog: MatDialog,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.categories$ = this.categoryService.getCategories();

    this.refreshDocuments$.pipe(
      tap(() => this.isLoadingSubject.next(true)),
      switchMap(() => this.documentService.getDocuments()),
      takeUntil(this.destroy$)
    ).subscribe(response => {
      this.dataSource.data = response.documents;
      this.isLoadingSubject.next(false);
    });
  }

  ngAfterViewInit(): void {
    this.dataSource.paginator = this.paginator;
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  refreshData(): void {
    this.refreshDocuments$.next();
  }

  onCategoryFilterChange(category: string): void {
    // In a real app, you would pass this to the service `getDocuments` method
    // For now, we filter client-side as a demonstration
    console.log('Filtering by category:', category);
    // this.refreshDataWithFilter({ category });
  }

  openUploadDialog(): void {
    const dialogRef = this.dialog.open(DocumentUploadComponent, {
      width: '500px',
      disableClose: true
    });

    dialogRef.afterClosed().subscribe(result => {
      if (result === 'success') {
        this.notificationService.showSuccess('Document uploaded successfully! Processing has started.');
        this.refreshData();
      }
    });
  }

  viewDocument(docId: string): void {
    this.router.navigate(['/documents', docId]);
  }

  reprocessDocument(docId: string): void {
    this.documentService.reprocessDocument(docId).subscribe(() => {
      this.notificationService.showSuccess('Document has been re-queued for processing.');
      this.refreshData();
    });
  }

  deleteDocument(docId: string): void {
    const dialogData: ConfirmationDialogData = {
      title: 'Confirm Deletion', message: 'Are you sure you want to move this document to the trash?'
    };
    const dialogRef = this.dialog.open(ConfirmationDialogComponent, { data: dialogData
    });

    dialogRef.afterClosed().subscribe(confirmed => {
      if (confirmed) {
        this.documentService.deleteDocument(docId).subscribe(() => {
          this.notificationService.showSuccess('Document moved to trash.');
          this.refreshData();
        });
      }
    });
  }
}
