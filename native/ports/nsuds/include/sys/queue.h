/* Tuikio: the tail-queue part of BSD's <sys/queue.h>, which glibc ships and musl does not.
 * Only what nsuds uses, with the same layout as the BSD macros. */
#ifndef TUIKIO_SYS_QUEUE_H
#define TUIKIO_SYS_QUEUE_H

#define TAILQ_HEAD(name, type) \
    struct name { struct type *tqh_first; struct type **tqh_last; }

#define TAILQ_ENTRY(type) \
    struct { struct type *tqe_next; struct type **tqe_prev; }

#define TAILQ_INIT(head) do { \
    (head)->tqh_first = NULL; \
    (head)->tqh_last = &(head)->tqh_first; \
} while (0)

#define TAILQ_FIRST(head) ((head)->tqh_first)
#define TAILQ_NEXT(elm, field) ((elm)->field.tqe_next)
#define TAILQ_LAST(head, headname) (*(((struct headname *)((head)->tqh_last))->tqh_last))
#define TAILQ_PREV(elm, headname, field) (*(((struct headname *)((elm)->field.tqe_prev))->tqh_last))

#define TAILQ_FOREACH(var, head, field) \
    for ((var) = TAILQ_FIRST(head); (var); (var) = TAILQ_NEXT(var, field))

#define TAILQ_INSERT_TAIL(head, elm, field) do { \
    (elm)->field.tqe_next = NULL; \
    (elm)->field.tqe_prev = (head)->tqh_last; \
    *(head)->tqh_last = (elm); \
    (head)->tqh_last = &(elm)->field.tqe_next; \
} while (0)

#define TAILQ_REMOVE(head, elm, field) do { \
    if ((elm)->field.tqe_next != NULL) \
        (elm)->field.tqe_next->field.tqe_prev = (elm)->field.tqe_prev; \
    else \
        (head)->tqh_last = (elm)->field.tqe_prev; \
    *(elm)->field.tqe_prev = (elm)->field.tqe_next; \
} while (0)

#endif
