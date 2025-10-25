import { Component } from '@angular/core';
import { GridApi, GridReadyEvent } from 'ag-grid-community';
import { AgGridModule } from 'ag-grid-angular';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { CategoryDialogComponent } from '../category-dialog/category-dialog.component';

@Component({
  selector: 'app-category-manager',
  templateUrl: './category-manager.component.html',
  styleUrls: ['./category-manager.component.scss'],
  standalone: true,
  imports: [AgGridModule, MatDialogModule]
})
export class CategoryManagerComponent {
  public columnDefs: any[] = [
    { headerName: 'Name', field: 'name', sortable: true, filter: true },
    { headerName: 'Description', field: 'description', sortable: true, filter: true },
    { headerName: 'Actions', field: 'actions', cellRenderer: this.actionsRenderer.bind(this) },
  ];

  public rowData: any[] = [
    { name: 'Invoice', description: 'Extracts invoice data' },
    { name: 'Receipt', description: 'Extracts receipt data' },
  ];

  private gridApi!: GridApi;

  constructor(public dialog: MatDialog) {}

  onGridReady(params: GridReadyEvent) {
    this.gridApi = params.api;
  }

  actionsRenderer(params: any) {
    const el = document.createElement('div');
    el.innerHTML = `
      <button class="btn-action">Edit</button>
      <button class="btn-action">Delete</button>
    `;
    return el;
  }

  openDialog(): void {
    const dialogRef = this.dialog.open(CategoryDialogComponent, {
      width: '500px'
    });

    dialogRef.afterClosed().subscribe(result => {
      console.log('The dialog was closed');
    });
  }
}