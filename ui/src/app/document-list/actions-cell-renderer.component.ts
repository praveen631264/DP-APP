import { Component } from '@angular/core';
import { ICellRendererAngularComp } from 'ag-grid-angular';
import { ICellRendererParams } from 'ag-grid-community';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';

@Component({
  selector: 'app-actions-cell-renderer',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div *ngIf="!isGrouping">
      <button class="btn-action">Process</button>
      <button class="btn-action">Delete</button>
      <button class="btn-action">Fail</button>
      <button class="btn-action">Restart</button>
      <button class="btn-action status-btn" (click)="viewWorkflow()">Status</button>
    </div>
  `
})
export class ActionsCellRendererComponent implements ICellRendererAngularComp {
  private params!: ICellRendererParams;
  public isGrouping = false;

  constructor(private router: Router) {}

  agInit(params: ICellRendererParams): void {
    this.params = params;
    this.isGrouping = !!params.node.group;
  }

  refresh(): boolean {
    return false;
  }

  viewWorkflow(): void {
    if (this.params.data?._id) {
      this.router.navigate(['/workflow-monitoring', this.params.data._id]);
    }
  }
}