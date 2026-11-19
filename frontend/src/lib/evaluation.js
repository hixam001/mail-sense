export function comparableEvaluation(data) {
  return Boolean(data?.same_test_ids === true && data.test_count > 0 && data.split_id && data.test_ids_sha256 &&
    ['multinomial', 'bernoulli'].every(name => {
      const model = data.models?.[name]
      const counts = model?.confusion_matrix
      return model?.model === name && model.positive_class === 'spam' && model.test_count === data.test_count &&
        model.split_id === data.split_id && model.test_ids_sha256 === data.test_ids_sha256 && counts &&
        ['tn', 'fp', 'fn', 'tp'].every(key => Number.isInteger(counts[key]) && counts[key] >= 0) &&
        counts.tn + counts.fp + counts.fn + counts.tp === data.test_count
    }))
}
