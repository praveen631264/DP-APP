import { Component, OnInit, OnDestroy, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { SelectionModel } from '@angular/cdk/collections';
import { MatTableDataSource, MatTableModule } from '@angular/material/table';
import { MatPaginator, MatPaginatorModule } from '@angular/material/paginator';
import { MatSort, MatSortModule } from '@angular/material/sort';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { Subscription } from 'rxjs';
import { Router } from '@angular/router';

import { DocumentService, PaginatedDocumentsResponse } from '../services/document.service';
import { Document } from '../models/document.model';
import { SocketService, DocumentStatusUpdate } from '../services/socket.service';
import { DocumentUploadComponent } from '../document-upload/document-upload.component';
import { StatusViewerComponent } from '../status-viewer/status-viewer.component';
import { ConfirmationDialogComponent } from '../confirmation-dialog/confirmation-dialog.component';
import { HttpClientModule } from '@angular/common/http';

@Component({
  selector: 'app-document-list',
  templateUrl: './document-list.component.html',
  styleUrls: ['./document-list.component.scss'],
  standalone: true,
  imports: [
    CommonModule,
    HttpClientModule,
    MatTableModule,
    MatPaginatorModule,
    MatSortModule,
    MatCheckboxModule,
    MatDialogModule,
    MatIconModule,
    MatButtonModule,
    DocumentUploadComponent,
    StatusViewerComponent
  ]
})
export class DocumentListComponent implements OnInit, OnDestroy {
  displayedColumns: string[] = ['select', 'filename', 'category', 'status', 'created_at', 'actions'];
  dataSource = new MatTableDataSource<Document>();
  selection = new SelectionModel<Document>(true, []);
  private socketSubscription!: Subscription;

  @ViewChild(MatPaginator) paginator!: MatPaginator;
  @ViewChild(MatSort) sort!: MatSort;

  constructor(
    private documentService: DocumentService,
    private socketService: SocketService,
    private router: Router,
    public dialog: MatDialog
  ) {}

  ngOnInit() {
    this.loadDocuments();
    this.socketSubscription = this.socketService.onDocumentStatusChanged().subscribe((data: DocumentStatusUpdate) => {
      this.updateRowData(data);
    });
  }

  ngOnDestroy() {
    if (this.socketSubscription) {
      this.socketSubscription.unsubscribe();
    }
  }

  loadDocuments() {
    this.documentService.getDocuments({ startRow: 0, endRow: 10000, sortModel: [], filterModel: {} })
      .subscribe((response: PaginatedDocumentsResponse) => {
        this.dataSource.data = response.items;
        this.dataSource.paginator = this.paginator;
        this.dataSource.sort = this.sort;
      }, error => {
        console.error('Failed to load documents for grid', error);
      });
  }

  updateRowData(data: DocumentStatusUpdate) {
    const index = this.dataSource.data.findIndex(doc => doc.id === data.doc_id);
    if (index > -1) {
      const updatedData = [...this.dataSource.data];
      updatedData[index].status = data.status;
      this.dataSource.data = updatedData;
    }
  }

  isAllSelected() {
    const numSelected = this.selection.selected.length;
    const numRows = this.dataSource.data.length;
    return numSelected === numRows;
  }

  masterToggle() {
    this.isAllSelected() ?
        this.selection.clear() :
        this.dataSource.data.forEach(row => this.selection.select(row));
  }

  viewDocument(doc: Document) {
    this.router.navigate(['/documents', doc.id]);
  }

  editDocument(doc: Document) {
    this.router.navigate(['/documents', doc.id, 'edit']);
  }

  deleteDocument(doc: Document) {
    const dialogRef = this.dialog.open(ConfirmationDialogComponent, {
      data: { message: `Are you sure you want to delete ${doc.filename}?` }
    });

    dialogRef.afterClosed().subscribe(result => {
      if (result) {
        this.documentService.deleteDocument(doc.id).subscribe(() => {
          this.dataSource.data = this.dataSource.data.filter(d => d.id !== doc.id);
        }, error => {
          console.error(`Failed to delete document ${doc.id}`, error);
        });
      }
    });
  }
}
