/** @moddoc
User analytics model with detailed metrics and segmentation.

This model processes raw user data to generate analytics-ready metrics:

1. **User Identification**: Normalizes user identifiers and emails
2. **Activity Metrics**: Calculates engagement scores and activity dates
3. **Segmentation**: Categorizes users by activity level and tenure
4. **Data Quality**: Filters out invalid and test accounts

## Upstream Dependencies
- `raw_users` - Raw user data from the source system
- `user_events` - Event stream data for activity calculations

## Downstream Usage
This model is used by:
- Dashboard reporting
- Marketing segmentation
- Customer success workflows
**/

with user_base as (
  select
    user_id /** @coldoc 
      Unique identifier for the user in the system.
      
      This is the primary key and is used for joins across all user-related tables.
    **/,
    
    lower(trim(email)) as email /** @coldoc
      Normalized email address (lowercase, trimmed whitespace).
      
      Used for customer communication and deduplication.
    **/,
    
    concat(first_name, ' ', last_name) as full_name /** @coldoc
      User's complete name, concatenated from first and last name fields.
    **/,
    
    created_at /** @coldoc 
      Timestamp when the user account was created.
      
      Used to calculate user tenure and cohort analysis.
    **/,
    
    date_diff('day', created_at, current_date) as days_since_signup /** @coldoc
      Number of days since the user signed up.
      
      This metric helps identify new vs. established users.
    **/
  from raw_users
  where 
    is_deleted = false
    and is_test_account = false
),

activity_metrics as (
  select
    user_id,
    count(*) as total_events /** @coldoc Total number of events recorded for this user **/,
    
    count(distinct date_trunc('day', event_timestamp)) as active_days /** @coldoc
      Count of distinct days with at least one event.
      
      Used to measure user engagement over time.
    **/,
    
    max(event_timestamp) as last_activity_at /** @coldoc
      Timestamp of the user's most recent activity.
      
      Used for churn analysis and re-engagement campaigns.
    **/
  from user_events
  group by user_id
),

final as (
  select
    b.user_id,
    b.email,
    b.full_name,
    b.created_at,
    b.days_since_signup,
    
    coalesce(m.total_events, 0) as total_events,
    coalesce(m.active_days, 0) as active_days,
    m.last_activity_at,
    
    case
      when coalesce(m.active_days, 0) >= 20 then 'high'
      when coalesce(m.active_days, 0) >= 5 then 'medium'
      else 'low'
    end as engagement_level /** @coldoc
      Categorizes users into high, medium, or low engagement levels.
      
      Calculated based on the number of active days:
      - high: 20+ active days
      - medium: 5-19 active days  
      - low: 0-4 active days
    **/,
    
    date_diff('day', m.last_activity_at, current_date) as days_since_last_activity /** @coldoc
      Days since the user's last recorded activity.
      
      A value of NULL indicates the user has never been active.
      Values > 30 may indicate a churned user.
    **/
    
  from user_base b
  left join activity_metrics m on b.user_id = m.user_id
)

select * from final
