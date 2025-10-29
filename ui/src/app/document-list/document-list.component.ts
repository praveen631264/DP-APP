import { Component, OnInit } from '@angular/core';
import { GridApi, GridReadyEvent, IServerSideDatasource, IServerSideGetRowsRequest } from 'ag-grid-community';
import { AgGridModule } from 'ag-grid-angular';
import { DocumentUploadComponent } from '../document-upload/document-upload.component';
import { StatusViewerComponent } from '../status-viewer/status-viewer.component';
import { CommonModule } from '@angular/common';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { DocumentService } from '../services/document.service';
import { HttpClientModule } from '@angular/common/http';
import { SocketService, DocumentStatusUpdate } from '../services/socket.service';
import { ActionsCellRendererComponent } from './actions-cell-renderer.component';

// Define the response structure from your service for better type safety
export interface PaginatedDocumentsResponse {
  items: any[];
  total: number;
}

@Component({
  selector: 'app-document-list',
  templateUrl: './document-list.component.html',
  styleUrls: ['./document-list.component.scss'],
  standalone: true,
  imports: [AgGridModule, DocumentUploadComponent, CommonModule, MatDialogModule, HttpClientModule]
})
export class DocumentListComponent implements OnInit {
  public columnDefs: any[] = [
    { headerName: 'Name', field: 'name', sortable: true, filter: true },
    { headerName: 'Category', field: 'category', sortable: true, filter: true, rowGroup: true, hide: true },
    { headerName: 'Status', field: 'status', cellRenderer: StatusViewerComponent },
    { headerName: 'Actions', field: 'actions', cellRenderer: ActionsCellRendererComponent, suppressMenu: true, sortable: false },
  ];

  public autoGroupColumnDef = {
    headerName: 'Group',
    minWidth: 250,
    field: 'name',
    valueGetter: function(params: any) {
      if (params.node.group) {
        return params.node.key;
      } else {
        return params.data[params.colDef.field];
      }
    },
    headerCheckboxSelection: true,
    cellRenderer: 'agGroupCellRenderer',
    cellRendererParams: {
      checkbox: true
    }
  };

  public gridApi!: GridApi;

  constructor(private documentService: DocumentService, private socketService: SocketService) {}

  ngOnInit() {
    this.socketService.onDocumentStatusChanged().subscribe((data: DocumentStatusUpdate) => {
      const rowNode = this.gridApi.getRowNode(data.doc_id);
      if (rowNode) {
        rowNode.data.status = data.status;
        this.gridApi.applyTransaction({ update: [rowNode.data] });
      }
    });
  }

  onGridReady(params: GridReadyEvent) {
    this.gridApi = params.api;
    const datasource = this.createServerSideDatasource();
    this.gridApi.setServerSideDatasource(datasource);
  }

  createServerSideDatasource(): IServerSideDatasource {
    return {
      getRows: (params) => {
        this.documentService.getDocuments(params.request)
          .subscribe((response: PaginatedDocumentsResponse) => {
            params.success({
              rowData: response.items,
              rowCount: response.total,
            });
          });
      },
    };
  }

}


