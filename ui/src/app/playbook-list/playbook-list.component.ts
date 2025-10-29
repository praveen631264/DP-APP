import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { Playbook, PlaybookService } from '../services/playbook.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-playbook-list',
  templateUrl: './playbook-list.component.html',
  styleUrls: ['./playbook-list.component.scss'],
  standalone: true,
  imports: [CommonModule, RouterModule]
})
export class PlaybookListComponent implements OnInit, OnDestroy {

  public playbooks: Playbook[] = [];
  private refreshSubscription!: Subscription;

  constructor(
    private playbookService: PlaybookService,
    private router: Router
  ) { }

  ngOnInit(): void {
    this.loadPlaybooks();
    this.refreshSubscription = this.playbookService.onRefreshNeeded().subscribe(() => {
      this.loadPlaybooks();
    });
  }

  ngOnDestroy(): void {
    if (this.refreshSubscription) {
      this.refreshSubscription.unsubscribe();
    }
  }

  loadPlaybooks(): void {
    this.playbookService.getPlaybooks().subscribe(data => {
      this.playbooks = data;
    });
  }

  createNewPlaybook(): void {
    this.router.navigate(['/playbooks/new']);
  }

  editPlaybook(id: string): void {
    this.router.navigate(['/playbooks', id, 'edit']);
  }

  deletePlaybook(id: string): void {
    if (confirm('Are you sure you want to delete this playbook?')) {
        this.playbookService.deletePlaybook(id);
    }
  }
}
