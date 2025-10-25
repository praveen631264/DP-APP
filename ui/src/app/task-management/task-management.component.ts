import { Component, OnInit } from '@angular/core';
import { AgGridModule } from 'ag-grid-angular';
import { GridApi, GridReadyEvent } from 'ag-grid-community';
import { TaskService } from '../services/task.service';
import { CommonModule } from '@angular/common';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { ConfirmationDialogComponent } from '../confirmation-dialog/confirmation-dialog.component';

@Component({
  selector: 'app-task-management',
  templateUrl: './task-management.component.html',
  styleUrls: ['./task-management.component.scss'],
  standalone: true,
  imports: [AgGridModule, CommonModule, MatDialogModule]
})
export class TaskManagementComponent implements OnInit {

  public columnDefs: any[] = [
    { headerName: 'ID', field: 'id', sortable: true, filter: true },
    { headerName: 'Name', field: 'name', sortable: true, filter: true },
    { headerName: 'Type', field: 'type', sortable: true, filter: true },
    { headerName: 'Status', field: 'status', sortable: true, filter: true },
    { headerName: 'Actions', field: 'actions', cellRenderer: this.actionsRenderer.bind(this) },
  ];

  public rowData: any[] = [];
  private gridApi!: GridApi;

  constructor(private taskService: TaskService, public dialog: MatDialog) { }

  ngOnInit(): void {
    this.taskService.getTasks().subscribe(tasks => {
      this.rowData = tasks;
    });
  }

  onGridReady(params: GridReadyEvent) {
    this.gridApi = params.api;
  }

  actionsRenderer(params: any) {
    const el = document.createElement('div');
    el.innerHTML = `
      <button class="btn-action stop-btn">Stop</button>
      <button class="btn-action restart-btn">Restart</button>
    `;

    const stopBtn = el.querySelector('.stop-btn');
    stopBtn?.addEventListener('click', () => {
      this.openConfirmationDialog('Stop Task', 'Are you sure you want to stop this task?', () => {
        this.taskService.stopTask(params.data.id).subscribe(() => {
          this.gridApi.applyTransaction({ update: [params.data] });
        });
      });
    });

    const restartBtn = el.querySelector('.restart-btn');
    restartBtn?.addEventListener('click', () => {
      this.openConfirmationDialog('Restart Task', 'Are you sure you want to restart this task?', () => {
        this.taskService.restartTask(params.data.id).subscribe(() => {
          this.gridApi.applyTransaction({ update: [params.data] });
        });
      });
    });

    return el;
  }

  openConfirmationDialog(title: string, message: string, onConfirm: () => void): void {
    const dialogRef = this.dialog.open(ConfirmationDialogComponent, {
      width: '400px',
      data: { title, message }
    });

    dialogRef.afterClosed().subscribe(result => {
      if (result) {
        onConfirm();
      }
    });
  }
}
