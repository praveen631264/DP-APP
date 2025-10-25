import { Component } from '@angular/core';
import { ICellRendererAngularComp } from 'ag-grid-angular';
import { ICellRendererParams } from 'ag-grid-community';

@Component({
  selector: 'app-actions-cell-renderer',
  templateUrl: './actions-cell-renderer.component.html',
  styleUrls: ['./actions-cell-renderer.component.scss']
})
export class ActionsCellRendererComponent implements ICellRendererAngularComp {
  
  public params!: ICellRendererParams;

  agInit(params: ICellRendererParams): void {
    this.params = params;
  }

  refresh(params: ICellRendererParams): boolean {
    this.params = params;
    // As we have no state, we don't need to refresh the component.
    // Return false to prevent the grid from destroying and recreating the component.
    return false;
  }

  onViewClick(): void {
    this.params.context.componentParent.viewDocument(this.params.data._id);
  }

  onDeleteClick(): void {
    this.params.context.componentParent.deleteDocument(this.params.data);
  }
}