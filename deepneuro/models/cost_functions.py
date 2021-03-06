import tensorflow as tf

from keras import backend as K


def cost_function_dict():

    return {'dice_coef': dice_coef,
            'dice_coef_loss': dice_coef_loss,
            }


def dice_coef_loss(y_true, y_pred):

    return (1 - dice_coef(y_true, y_pred))


def dice_coef(y_true, y_pred, smooth=1.):

    y_true_f = K.flatten(y_true)
    y_pred_f = K.flatten(y_pred)
    intersection = K.sum(y_true_f * y_pred_f)
    return (2. * intersection + smooth) / (K.sum(y_true_f) + K.sum(y_pred_f) + smooth)


def wasserstein_loss(model, discriminator, discriminator_fake_logits, discriminator_real_logits, synthetic_images, reference_images, gradient_penalty_weight=10, name='discriminator', dim=2, depth=None, transition=False, alpha_transition=0):

    if depth is None:
        depth = model.depth

    D_loss = tf.reduce_mean(discriminator_fake_logits) - tf.reduce_mean(discriminator_real_logits)
    G_loss = -tf.reduce_mean(discriminator_fake_logits)

    differences = synthetic_images - reference_images
    alpha = tf.random_uniform(shape=[tf.shape(differences)[0]] + [1] * (dim + 1), minval=0., maxval=1.)
    interpolates = reference_images + (alpha * differences)
    _, interpolates_logits = discriminator(model, interpolates, reuse=True, depth=depth, name=name, transition=transition, alpha_transition=alpha_transition)
    gradients = tf.gradients(interpolates_logits, [interpolates])[0]

    slopes = tf.sqrt(tf.reduce_sum(tf.square(gradients), reduction_indices=range(1, 2 + model.dim)))
    gradient_penalty = tf.reduce_mean((slopes - 1.) ** 2)
    tf.summary.scalar("gp_loss", gradient_penalty)

    D_origin_loss = D_loss
    D_loss += 10 * gradient_penalty
    D_loss += 0.001 * tf.reduce_mean(tf.square(discriminator_real_logits - 0.0))

    return [D_loss], [G_loss], [D_origin_loss]