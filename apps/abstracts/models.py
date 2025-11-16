from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Abstract(models.Model):
    """Scientific article abstract"""
    
    # Publication type choices
    JOURNAL = 'J'
    CONFERENCE = 'C'
    BOOK = 'B'
    SERIES = 'S'
    PUBLICATION_TYPE_CHOICES = [
        (JOURNAL, 'Journal Article'),
        (CONFERENCE, 'Conference Paper'),
        (BOOK, 'Book Chapter'),
        (SERIES, 'Series'),
    ]
    
    # Basic information
    title = models.TextField()
    authors = models.TextField()
    abstract_text = models.TextField()
    keywords = models.TextField(blank=True)
    doi = models.CharField(max_length=200, blank=True, db_index=True)
    publication_year = models.IntegerField(null=True, blank=True)
    publication_type = models.CharField(
        max_length=1, 
        choices=PUBLICATION_TYPE_CHOICES, 
        default=JOURNAL,
        db_index=True
    )
    journal = models.CharField(max_length=500, blank=True)
    url = models.URLField(max_length=500, blank=True)
    
    # Bibliometric information (from Web of Science)
    affiliations = models.TextField(
        blank=True, 
        help_text="Author addresses/affiliations (C1 field from WoS)"
    )
    times_cited = models.IntegerField(
        default=0, 
        help_text="Number of times cited (TC field from WoS)",
        db_index=True
    )
    wos_categories = models.TextField(
        blank=True,
        help_text="Web of Science Categories (WC field from WoS)"
    )
    research_areas = models.TextField(
        blank=True,
        help_text="Research Areas (SC field from WoS)"
    )
    
    # Classification metadata
    required_classifications = models.IntegerField(
        default=5, 
        validators=[MinValueValidator(1), MaxValueValidator(20)]
    )
    current_classifications_count = models.IntegerField(default=0, db_index=True)
    difficulty_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    consensus_reached = models.BooleanField(default=False, db_index=True)
    
    # Distribution tracking
    times_shown = models.IntegerField(default=0, help_text="Number of times shown to users")
    last_shown_at = models.DateTimeField(null=True, blank=True)
    
    # For gold users
    is_gold_standard = models.BooleanField(default=False, db_index=True)
    gold_classifications_complete = models.BooleanField(default=False)
    
    # Control
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['current_classifications_count', '-created_at']
        verbose_name = 'Abstract'
        verbose_name_plural = 'Abstracts'
        indexes = [
            models.Index(fields=['doi']),
            models.Index(fields=['is_gold_standard', 'gold_classifications_complete']),
            models.Index(fields=['current_classifications_count', 'consensus_reached']),
            models.Index(fields=['is_active', 'is_gold_standard', 'current_classifications_count']),
            models.Index(fields=['publication_type', 'publication_year']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(current_classifications_count__gte=0),
                name='positive_classification_count'
            ),
            models.CheckConstraint(
                check=models.Q(required_classifications__gte=1),
                name='minimum_required_classifications'
            ),
        ]
    
    def __str__(self):
        if self.doi:
            return f"{self.doi}: {self.title[:50]}..."
        return f"{self.title[:60]}..."
    
    def needs_more_classifications(self):
        """Check if it needs more classifications"""
        return self.current_classifications_count < self.required_classifications and not self.consensus_reached
    
    def calculate_priority_score(self):
        """
        Calculate priority score for assignment (lower is higher priority)
        Considers: number of classifications, times shown, difficulty
        """
        base_score = self.current_classifications_count * 100
        shown_penalty = self.times_shown * 2  # Small penalty for being shown multiple times
        difficulty_bonus = -self.difficulty_score * 10  # Harder ones get slight priority
        
        return base_score + shown_penalty + difficulty_bonus
    
    def mark_as_shown(self):
        """Increment times shown counter"""
        from django.utils import timezone
        self.times_shown += 1
        self.last_shown_at = timezone.now()
        self.save(update_fields=['times_shown', 'last_shown_at'])
